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

    # Extract the name of every tool. This will potentially be outdated if
    # someone has added something to the main file. this is intentional.
    locked_tools = [x['name'] for x in locked['tools']]

    # As here we add any new tools in.
    for tool in unlocked['tools']:
        if tool['name'] not in locked_tools:
            # Add it to the set of locked tools.
            locked['tools'].append(tool)

    with open(fn + '.lock', 'w') as handle:
        yaml.dump(locked, handle, default_flow_style=False)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('fn', type=argparse.FileType('r'), help="Tool.yaml file")
    parser.add_argument('--dry-run', action='store_true', help="Trust all listed tools in the file, i.e. add the latest changest for them.")
    args = parser.parse_args()
    update_file(args.fn.name, dry=args.dry_run)
