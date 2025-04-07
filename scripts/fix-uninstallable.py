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

import argparse
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

from bioblend import galaxy, toolshed
from galaxy.tool_util.loader_directory import load_tool_sources_from_path


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
        proc = subprocess.run(cmd, cwd = repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.returncode == 0, f"failed {' '.join(cmd)}"

def get_all_revisions(toolshed_url: str, name: str, owner: str) -> List[str]:
    repo_path = f"/tmp/repos/toolshed-{owner}-{name}"
    clone(toolshed_url, name, owner, repo_path)
    cmd = ["hg", "update", "tip"]
    proc = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
    assert proc.returncode == 0, f"failed {' '.join(cmd)}"
    cmd = ["hg", "log", "--template", "{node|short}\n"]
    assert proc.returncode == 0, f"failed {' '.join(cmd)}"
    result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
    return list(reversed(result.stdout.splitlines()))


def get_all_versions(
    toolshed_url: str, name: str, owner: str, revisions: List[str]
) -> Dict[str, Set[Tuple[str, str]]]:
    repo_path = f"/tmp/repos/toolshed-{owner}-{name}"
    clone(toolshed_url, name, owner, repo_path)

    versions: Dict[str, Set[Tuple[str, str]]] = {}
    for r in revisions:
        cmd = ["hg", "update", r]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        versions[r] = set()
        for _, tool in load_tool_sources_from_path(repo_path):
            versions[r].add((tool.parse_id(), tool.parse_version()))

    return versions


def fix_uninstallable(lockfile_name: str, toolshed_url: str, galaxy_url: Optional[str] = None) -> None:
    ts = toolshed.ToolShedInstance(url=toolshed_url)
    installed_tools = {}
    if galaxy_url:
        gi = galaxy.GalaxyInstance(url=galaxy_url, key=None)
        for t in gi.toolshed.get_repositories():
            if (t['name'], t['owner']) not in installed_tools:
                installed_tools[(t['name'], t['owner'])] = set()
            # TODO? could also check for 'status': 'Installed'
            if t['deleted'] or t['uninstalled']:
                continue
            installed_tools[(t['name'], t['owner'])].add(t['changeset_revision'])

    with open(lockfile_name) as f:
        lockfile = yaml.safe_load(f)
        locked_tools = lockfile["tools"]

    for i, locked_tool in enumerate(locked_tools):
        name = locked_tool["name"]
        owner = locked_tool["owner"]

        # get ordered_installable_revisions from oldest to newest
        ordered_installable_revisions = (
            ts.repositories.get_ordered_installable_revisions(name, owner)
        )

        if len(set(locked_tool["revisions"]) - set(ordered_installable_revisions)):
            all_revisions = get_all_revisions(toolshed_url, name, owner)
            all_versions = get_all_versions(toolshed_url, name, owner, all_revisions)

        to_remove = []
        to_append = []
        for cur in locked_tool["revisions"]:
            if cur in ordered_installable_revisions:
                continue
            assert cur in all_revisions, f"{cur} is not a valid revision of {name} {owner}"
            start = all_revisions.index(cur)
            nxt = None
            for i in range(start, len(all_revisions)):
                if all_revisions[i] in ordered_installable_revisions:
                    nxt = all_revisions[i]
                    break

            assert nxt, f"Could not determine next revision for {cur} {name} {owner}"
            assert all_versions[cur] == all_versions[nxt], f"{name},{onwer} {cur} {next} have unequal versions"

            print(f"remove {cur} in favor of {nxt} {name} {owner}")
            to_remove.append(cur)
            if nxt not in locked_tool["revisions"]:
                print(f"adding {nxt} which was absent so far {name} {owner}")
                to_append.append(nxt)
            elif galaxy_url:
                assert (name, owner) in installed_tools
                assert cur not in installed_tools[(name, owner)], f"{name},{owner} {cur} still installed on {galaxy_url}"

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
    parser.add_argument('--galaxy_url', default=None, required=False, help="Galaxy instance to check")
    args = parser.parse_args()
    fix_uninstallable(args.lockfile.name, args.toolshed, args.galaxy_url)
