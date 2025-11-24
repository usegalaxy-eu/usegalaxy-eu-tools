import argparse
import logging
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

import yaml
from bioblend import toolshed

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def retry_with_backoff(func, *args, **kwargs):
    MAX_RETRIES = 5
    backoff = 2

    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except Exception as e:
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
                    continue
            raise e
    raise Exception("Retry failed after max attempts")


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
    lockfile_path = Path(lockfile_name)
    with open(lockfile_path) as f:
        lockfile = yaml.safe_load(f) or {}
    locked_tools = lockfile.get("tools", [])
    total = len(locked_tools)

    uninstallable_file = lockfile_path.with_name(
        lockfile_path.name.replace(".yaml.lock", ".uninstallable_revisions.yaml")
    )

    removed_map = defaultdict(set)
    try:
        with open(uninstallable_file) as f:
            uninstallable_data = yaml.safe_load(f) or {}
            for t in uninstallable_data.get("tools", []):
                removed_map[(t["name"], t["owner"])] = set(
                    t.get("removed_revisions", [])
                )
    except FileNotFoundError:
        pass

    logger.info(f"Processing {total} tools from {lockfile_path.name}...")
    changed, skipped = 0, 0

    for i, tool in enumerate(locked_tools):
        if i % 10 == 0:
            logger.info(
                f"Progress: {i}/{total} tools ({skipped} skipped, {changed} changed)"
            )

        name, owner = tool.get("name"), tool.get("owner")
        current_revisions = set(tool.get("revisions", []))
        try:
            installable_list = retry_with_backoff(
                ts.repositories.get_ordered_installable_revisions, name, owner
            )
        except Exception as e:
            logger.warning(f"{name},{owner}: could not get installable revisions ({e})")
            continue

        uninstallable = current_revisions - set(installable_list)
        if not uninstallable:
            skipped += 1
            continue

        all_revs = list(uninstallable) + installable_list
        version_cache = fetch_versions_parallel(ts, name, owner, all_revs)

        installable_signatures = {}
        for rev in installable_list:
            sig = frozenset(version_cache.get(rev, []))
            if sig:
                installable_signatures[sig] = rev
        to_remove = set()

        for cur in uninstallable:
            cur_sig = frozenset(version_cache.get(cur, []))
            if not cur_sig:
                if installable_list:
                    nxt = installable_list[-1]
                    logger.info(f"{name},{owner}: unverifiable {cur}, keeping {nxt}")
                    to_remove.add(cur)
                    continue

            nxt = installable_signatures.get(cur_sig)

            if not nxt:
                logger.warning(
                    f"{name},{owner}: no matching installable revision for {cur}"
                )
                sys.exit(1)

            logger.info(f"{name},{owner}: removing {cur} in favor of {nxt}")
            if nxt not in current_revisions:
                tool["revisions"].append(nxt)
            to_remove.add(cur)

        if to_remove:
            changed += 1
            tool["revisions"] = sorted(set(tool["revisions"]) - to_remove)
            removed_map[(name, owner)].update(to_remove)

    logger.info(
        f"Completed: {total} tools processed, {skipped} skipped, {changed} changed"
    )

    with open(lockfile_path, "w") as f:
        yaml.dump(lockfile, f, sort_keys=False, default_flow_style=False)

    uninstallable_output = {
        "tools": [
            {"name": n, "owner": o, "removed_revisions": sorted(revs)}
            for (n, o), revs in removed_map.items()
        ]
    }
    with open(uninstallable_file, "w") as f:
        yaml.dump(uninstallable_output, f, sort_keys=False, default_flow_style=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("lockfile", help="Tool.yaml.lock file path")
    parser.add_argument(
        "--toolshed", default="https://toolshed.g2.bx.psu.edu", help="Toolshed base URL"
    )
    args = parser.parse_args()

    fix_uninstallable(args.lockfile, args.toolshed)
