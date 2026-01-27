# check all revisions in the lockfile if they are installable
# remove if not and the next installable version is added
#
# the script only updates the lock file and does not install
# or uninstall any tools from a Galaxy instance
#
# backgroud for each version there can be only one revision installed
# (multiple revisions with the same version happen eg if the version
# is not bumbed)
#
# revisions that became uninstallable can be safely removed since
#
# - tool revision can not be executed anyway
# - also if another instance requests to install then the latest
#   revision with the same version will be installed
#
# the script queries the TS to get_ordered_installable_revisions
# and clones (to /tmp/) the mercurial repos to get all revisions
# (the later is opnly done for tools with revisions that are not
# installable)
#
# For each revision cur that has been replaced by nxt
# - check that the tool versions of the revisons are really the same
# - if cur and nxt are in the lock file cur is removed
#   - if a Galaxy URL is given it is checked that cur is not installed
# - if only cur in in the list then cur is removed and nxt is added
#
# The tool logs INFO messages for each removed / added revision
# 
# In addition there are several possible WARNING messages that
# require manual checks
# 
# NAME,REPO CURRENT NEXT have unequal versions
# - the currently considered revision is not removed because
#   not-bumping is not the cause for being not-intstallable,
#   i.e. the currently considered revision is not intstallable
#   and the next installable revision has a different version
#
# NAME,REPO CURRENT still installed on GALAXY_URL
# - the currently considered revision is not removed because
#   it is still installed on the given Galaxy instance
# 
# NAME,REPO Adjacent installable revisions CURRENT NEXT have equal versions
# - the currently considered revision is installable and
#   has the same version as the next installable revision
#   i.e. maybe it should not be installable?
#
# NAME,REPO Could not determine next revision for CURRENT
# - CURRENT is not installable and no installable revision
#   has been found in the TS (that has been added after CURRENT)
#
# NAME,REPO Could not determine versions for CURRENT
# - The versions for revision CURRENT could not be determined.
#   This means that the tool repo did not contain a parsable tool.

import argparse
import logging
import subprocess
import os.path
import yaml
from typing import (
    Dict,
    List,
    Optional,
    Set,
    Tuple,
)

import bioblend
from bioblend import galaxy, toolshed
from galaxy.tool_util.loader_directory import load_tool_sources_from_path


logger = logging.getLogger()


def clone(toolshed_url: str, name: str, owner: str, repo_path: str) -> None:
    if not os.path.exists(repo_path):
        cmd = [
            "hg",
            "clone",
            f"{toolshed_url}/repos/{owner}/{name}",
            repo_path,
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        cmd = ["hg", "pull", "-u"]
        proc = subprocess.run(
            cmd, cwd=repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    assert proc.returncode == 0, f"failed {' '.join(cmd)} in {repo_path}"


def get_all_revisions(toolshed_url: str, name: str, owner: str) -> List[str]:
    repo_path = f"/tmp/repos/{os.path.basename(toolshed_url)}-{owner}-{name}"
    clone(toolshed_url, name, owner, repo_path)
    cmd = ["hg", "update", "tip"]
    proc = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
    assert proc.returncode == 0, f"failed {' '.join(cmd)} in {repo_path}"
    cmd = ["hg", "log", "--template", "{node|short}\n"]
    assert proc.returncode == 0, f"failed {' '.join(cmd)} in {repo_path}"
    result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
    return list(reversed(result.stdout.splitlines()))


def get_all_versions(
    toolshed_url: str, name: str, owner: str, revisions: List[str]
) -> Dict[str, Set[Tuple[str, str]]]:
    def silent_load_exception_handler(path, exc_info):
        pass

    repo_path = f"/tmp/repos/{os.path.basename(toolshed_url)}-{owner}-{name}"
    clone(toolshed_url, name, owner, repo_path)

    versions: Dict[str, Set[Tuple[str, str]]] = {}
    for r in revisions:
        cmd = ["hg", "update", r]
        subprocess.run(
            cmd, cwd=repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        versions[r] = set()
        for _, tool in load_tool_sources_from_path(
            repo_path,
            recursive=True,
            load_exception_handler=silent_load_exception_handler,
        ):
            versions[r].add((tool.parse_id(), tool.parse_version()))

        if len(versions[r]) == 0:
            logger.warning(f"{name},{owner} Could not determine versions for {r}")

    return versions


def get_next(
    cur: str, all_revisions: List[str], ordered_installable_revisions: List[str]
) -> Optional[str]:
    start = all_revisions.index(cur) + 1
    nxt = None
    for i in range(start, len(all_revisions)):
        if all_revisions[i] in ordered_installable_revisions:
            nxt = all_revisions[i]
            break
    return nxt


def fix_uninstallable(
    lockfile_name: str, toolshed_url: str, galaxy_url: Optional[str] = None, add:bool = False
) -> None:
    ts = toolshed.ToolShedInstance(url=toolshed_url)
    installed_tools: Dict[Tuple[str, str], Set[str]] = {}
    if galaxy_url:
        gi = galaxy.GalaxyInstance(url=galaxy_url, key=None)
        for t in gi.toolshed.get_repositories():
            if (t["name"], t["owner"]) not in installed_tools:
                installed_tools[(t["name"], t["owner"])] = set()
            # TODO? could also check for 'status': 'Installed'
            if t["deleted"] or t["uninstalled"]:
                continue
            installed_tools[(t["name"], t["owner"])].add(t["changeset_revision"])

    with open(lockfile_name) as f:
        lockfile = yaml.safe_load(f)
        locked_tools = lockfile["tools"]

    for i, locked_tool in enumerate(locked_tools):
        name = locked_tool["name"]
        owner = locked_tool["owner"]

        # get ordered_installable_revisions from oldest to newest
        try:
            ordered_installable_revisions = (
                ts.repositories.get_ordered_installable_revisions(name, owner)
            )
        except bioblend.ConnectionError:
            logger.warning(
                f"{name},{owner} Could not determine intstallable revisions for "
            )
            continue

        if len(set(locked_tool["revisions"]) - set(ordered_installable_revisions)):
            all_revisions = get_all_revisions(toolshed_url, name, owner)
            all_versions = get_all_versions(toolshed_url, name, owner, all_revisions)
        else:
            continue

        to_remove = []
        to_append = []
        for cur in locked_tool["revisions"]:
            assert (
                cur in all_revisions
            ), f"{cur} is not a valid revision of {name} {owner}"
            nxt = get_next(cur, all_revisions, ordered_installable_revisions)
            if cur in ordered_installable_revisions:
                if nxt and all_versions[cur] == all_versions[nxt]:
                    logger.warning(
                        f"{name},{owner} Adjacent installable revisions {cur} {nxt} have equal versions"
                    )
                continue

            if not nxt:
                logger.warning(
                    f"{name},{owner} Could not determine next revision for {cur}"
                )
                continue
            if all_versions[cur] != all_versions[nxt]:
                logger.warning(f"{name},{owner} {cur} {nxt} have unequal versions")
                continue

            if nxt not in locked_tool["revisions"]:
                if add:
                    logger.info(f"{name},{owner} remove {cur} in favor of {nxt} ")
                    logger.info(f"{name},{owner} Adding {nxt} which was absent so far")
                    to_append.append(nxt)
                    to_remove.append(cur)
            elif galaxy_url:
                assert (name, owner) in installed_tools
                if cur in installed_tools[(name, owner)]:
                    logger.warning(
                        f"{name},{owner} {cur} still installed on {galaxy_url}"
                    )
                    continue
            else:
                logger.info(f"{name},{owner} remove {cur} in favor of {nxt} ")
                to_remove.append(cur)

        for r in to_remove:
            locked_tool["revisions"].remove(r)
        locked_tool["revisions"].extend(to_append)

    with open(lockfile_name, "w") as handle:
        yaml.dump(lockfile, handle, default_flow_style=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "lockfile", type=argparse.FileType("r"), help="Tool.yaml.lock file"
    )
    parser.add_argument(
        "--toolshed",
        default="https://toolshed.g2.bx.psu.edu",
        help="Toolshed to test against",
    )
    parser.add_argument(
        "--galaxy_url", default=None, required=False, help="Galaxy instance to check. If given it is checked if the not-installable revision is still installed."
    )
    parser.add_argument(
        "--add", default=False, action="store_true", help="Add new intstallable revisions if missing, default is not to add it and also keep the uninstallable one"
    )
    args = parser.parse_args()

    logger.setLevel(logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("bioblend").setLevel(logging.WARNING)
    logging.getLogger("PIL.Image").setLevel(logging.WARNING)
    # otherwise tool loading errors (of there are other xml files that can't be parsed?) are still reported
    logging.getLogger("galaxy.util").disabled = True
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    fix_uninstallable(args.lockfile.name, args.toolshed, args.galaxy_url, args.add)
