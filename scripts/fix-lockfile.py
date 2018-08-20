import yaml
import os
import glob
import copy
import argparse

from bioblend import toolshed


ts = toolshed.ToolShedInstance(url='https://toolshed.g2.bx.psu.edu')


def update_file(fn, dry):
    with open(fn, 'r') as handle:
        unlocked = yaml.load(handle)
    # If a lock file exists, load it from that file
    if os.path.exists(fn + '.lock'):
        with open(fn + '.lock', 'r') as handle:
            locked = yaml.load(handle)
    else:
        # Otherwise just clone the "unlocked" list.
        locked = copy.deepcopy(unlocked)

    # We will place entries in a cleaned lockfile, removing defunct entries, etc.
    clean_lockfile = copy.deepcopy(locked)
    clean_lockfile['tools'] = []

    # As here we add any new tools in.
    for tool in unlocked['tools']:
        # If we have an existing locked copy, we'll just use that.
        locked_tools = [x for x in locked['tools'] if x['name'] == tool['name'] and x['owner'] == tool['owner']]
        # If there are no copies of it seen in the lockfile, we'll just copy it
        # over directly, without a reivision. Another script will fix that.
        if len(locked) == 0:
            # new tool, just add directly.
            clean_lockfile['tools'].append(tool)
            continue

        # Otherwise we hvae one or more locked versions so we'll harmonise +
        # reduce. Revisions are the only thing that could be variable.
        # Name/section/owner should not be. If they are, we take original human
        # edited .yaml file as source of truth.

        revisions = []
        for locked_tool in locked_tools:
            for revision in locked_tool.get('revisions', []):
                revisions.append(revision)

        new_tool = {
            'name': tool['name'],
            'owner': tool['owner'],
            'tool_panel_section_label': tool['tool_panel_section_label'],
            'revisions': list(set(revisions)),  # Cast to list for yaml serialization
        }

        clean_lockfile['tools'].append(new_tool)

    with open(fn + '.lock', 'w') as handle:
        yaml.dump(clean_lockfile, handle, default_flow_style=False)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('fn', type=argparse.FileType('r'), help="Tool.yaml file")
    parser.add_argument('--dry-run', action='store_true', help="Trust all listed tools in the file, i.e. add the latest changest for them.")
    args = parser.parse_args()
    update_file(args.fn.name, dry=args.dry_run)
