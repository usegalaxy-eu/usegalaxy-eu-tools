# check all revisions in the lockfile if they are still installed
# at a given Galaxy instance and remove them from the lock file if not
#
# The tool logs INFO messages for each removed revision
# and prints WARNING messages for tools that are not installed
# anymore

import argparse
import logging
import yaml
from typing import (
    Dict,
    Set,
    Tuple,
)

from bioblend import galaxy


logger = logging.getLogger()


def fix_not_installed(lockfile_name: str, galaxy_url: str) -> None:

    gi = galaxy.GalaxyInstance(url=galaxy_url, key=None)
    installed_tools: Dict[Tuple[str, str], Set[str]] = {}
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
        if (name, owner) not in installed_tools:
            logger.warning(f"{name},{owner} not installed anymore")
            continue

        to_remove = []
        for cur in locked_tool["revisions"]:
            if cur not in installed_tools[(name, owner)]:
                logger.info(f"{name},{owner} remove {cur} ")
                to_remove.append(cur)

        for r in to_remove:
            locked_tool["revisions"].remove(r)
        locked_tool["revisions"] = sorted(list(set(map(str, locked_tool["revisions"]))))

    with open(lockfile_name, "w") as handle:
        yaml.dump(lockfile, handle, default_flow_style=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "lockfile", type=argparse.FileType("r"), help="Tool.yaml.lock file"
    )
    parser.add_argument(
        "--galaxy_url",
        help="Galaxy instance to check. If given it is checked if the not-installable revision is still installed.",
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

    fix_not_installed(args.lockfile.name, args.galaxy_url)
