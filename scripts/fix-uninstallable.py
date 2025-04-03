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

import argparse
import subprocess
import os.path
import yaml

from bioblend import toolshed
from galaxy.tool_util.loader_directory import load_tool_sources_from_path


def clone(toolshed_url, name, owner, repo_path):
    if not os.path.exists(repo_path):
        cmd = [
            "hg",
            "clone",
            f"{toolshed_url}/repos/{owner}/{name}",
            repo_path,
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def get_all_revisions(toolshed_url, name, owner):
    repo_path = f"/tmp/toolshed-{owner}-{name}"
    clone(toolshed_url, name, owner, repo_path)
    cmd = ["hg", "update", "tip"]
    cmd = ["hg", "log", "--template", "{node|short}\n"]
    result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
    return list(reversed(result.stdout.splitlines()))


def get_all_versions(toolshed_url, name, owner, revisions):
    repo_path = f"/tmp/toolshed-{owner}-{name}"
    clone(toolshed_url, name, owner, repo_path)

    versions = {}
    for r in revisions:
        cmd = ["hg", "update", r]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        versions[r] = set()
        for _, tool in load_tool_sources_from_path(repo_path):
            versions[r].add((tool.parse_id(), tool.parse_version()))

    return versions


def fix_uninstallable(lockfile_name, toolshed_url):
    ts = toolshed.ToolShedInstance(url=toolshed_url)

    with open(lockfile_name) as f:
        lockfile = yaml.safe_load(f)
        tools = lockfile["tools"]

    for i, tool in enumerate(tools):
        name = tool["name"]
        owner = tool["owner"]

        # get ordered_installable_revisions from oldest to newest
        ordered_installable_revisions = (
            ts.repositories.get_ordered_installable_revisions(name, owner)
        )

        if len(set(tool["revisions"]) - set(ordered_installable_revisions)):
            all_revisions = get_all_revisions(toolshed_url, name, owner)
            # all_versions = get_all_versions(toolshed_url, name, owner, all_revisions)

        to_remove = []
        to_append = []
        for cur in tool["revisions"]:
            if cur in ordered_installable_revisions:
                continue
            if cur not in all_revisions:
                print(f"{cur} is not a valid revision of {name} {owner}")
                to_remove.append(cur)
                continue
            start = all_revisions.index(cur)
            nxt = None
            for i in range(start, len(all_revisions)):
                if all_revisions[i] in ordered_installable_revisions:
                    nxt = all_revisions[i]
            if nxt:
                print(f"remove {cur} in favor of {nxt} {name} {owner}")
                to_remove.append(cur)
                if nxt not in tool["revisions"]:
                    print(f"adding {nxt} which was absent so far {name} {owner}")
                    to_append(nxt)
            else:
                print(f"Could not determine next revision for {cur} {name} {owner}")

        for r in to_remove:
            tool["revisions"].remove(r)
        tool["revisions"].extend(to_append)

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
    args = parser.parse_args()
    fix_uninstallable(args.lockfile.name, args.toolshed)
