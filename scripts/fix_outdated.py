import argparse
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import yaml
from bioblend import toolshed

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def retry_with_backoff(func, *args, **kwargs):
    MAX_RETRIES = 5
    backoff = 2
    last_exception = None

    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            error_msg = str(e)
            if any(
                code in error_msg
                for code in ["502", "503", "504", "timed out", "timeout", "Connection"]
            ):
                if attempt < MAX_RETRIES - 1:
                    logger.warning(
                        f"Attempt {attempt + 1}/{MAX_RETRIES} failed: {error_msg}. Retrying in {backoff}s..."
                    )
                    time.sleep(backoff)
                    backoff = min(backoff * 2, 60)
                else:
                    logger.error(f"All {MAX_RETRIES} attempts failed")
            else:
                raise

    if last_exception:
        raise last_exception
    raise Exception("Retry failed with no exception captured")


def get_tool_versions(ts, name, owner, revision):
    versions = set()

    try:
        repo_metadata = retry_with_backoff(
            ts.repositories.get_repository_revision_install_info, name, owner, revision
        )
        if isinstance(repo_metadata, list) and len(repo_metadata) > 1:
            for tool in repo_metadata[1].get("valid_tools", []):
                if "id" in tool and "version" in tool:
                    versions.add((tool["id"], tool["version"]))
    except Exception as e:
        logger.warning(f"{name},{owner}: failed to fetch {revision} ({e})")
        sys.exit(1)
    return versions


def fetch_versions_parallel(ts, name, owner, revisions, max_workers=10):
    version_cache = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(get_tool_versions, ts, name, owner, rev): rev
            for rev in revisions
        }
        for future in as_completed(futures):
            rev = futures[future]
            try:
                version_cache[rev] = future.result()
            except Exception as e:
                logger.warning(f"{name},{owner}: error fetching {rev} ({e})")
                sys.exit(1)
    return version_cache


def fix_uninstallable(lockfile_name, toolshed_url):
    ts = toolshed.ToolShedInstance(url=toolshed_url)
    with open(lockfile_name) as f:
        lockfile = yaml.safe_load(f) or {}
    locked_tools = lockfile.get("tools", [])
    total = len(locked_tools)

    logger.info(f"Processing {total} tools from {lockfile_name}...")
    changed, skipped = 0, 0

    for i, tool in enumerate(locked_tools):
        if i % 10 == 0:
            logger.info(
                f"Progress: {i}/{total} tools ({skipped} skipped, {changed} changed)"
            )

        name, owner = tool.get("name"), tool.get("owner")
        revisions = tool.get("revisions", [])
        try:
            installable = retry_with_backoff(
                ts.repositories.get_ordered_installable_revisions, name, owner
            )
        except Exception as e:
            logger.warning(f"{name},{owner}: could not get installable revisions ({e})")
            continue

        uninstallable = set(revisions) - set(installable)
        if not uninstallable:
            skipped += 1
            continue

        all_revs = list(uninstallable) + list(installable)
        version_cache = fetch_versions_parallel(ts, name, owner, all_revs)

        to_remove = []
        for cur in uninstallable:
            cur_versions = version_cache.get(cur, set())
            if not cur_versions:
                if installable:
                    nxt = installable[0]
                    logger.info(f"{name},{owner}: unverifiable {cur}, keeping {nxt}")
                    to_remove.append(cur)
                continue

            nxt = next(
                (
                    cand
                    for cand in installable
                    if version_cache.get(cand) == cur_versions
                ),
                None,
            )

            if not nxt:
                logger.warning(
                    f"{name},{owner}: no matching installable revision for {cur}"
                )
                sys.exit(1)

            logger.info(
                f"{name},{owner}: removing {cur} {'in favor of ' + nxt if nxt in revisions else 'with no installable alternative found'}"
            )
            to_remove.append(cur)

        if to_remove:
            changed += 1
            tool["revisions"] = sorted(set(r for r in revisions if r not in to_remove))

    logger.info(
        f"Completed: {total} tools processed, {skipped} skipped, {changed} changed"
    )

    with open(lockfile_name, "w") as f:
        yaml.dump(lockfile, f, sort_keys=False, default_flow_style=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "lockfile", type=argparse.FileType("r"), help="Tool.yaml.lock file"
    )
    parser.add_argument(
        "--toolshed", default="https://toolshed.g2.bx.psu.edu", help="Toolshed base URL"
    )
    args = parser.parse_args()

    fix_uninstallable(args.lockfile.name, args.toolshed)
