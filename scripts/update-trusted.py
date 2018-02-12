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

    # Update any locked tools.
    for tool in locked['tools']:
        # Should we trust this?
        # get CR
        try:
            revs = ts.repositories.get_ordered_installable_revisions(tool['name'], tool['owner'])
        except Exception as e:
            print(e)
            continue

        print("  Found newer revision of %s/%s (%s)" % (tool['owner'], tool['name'], revs[0]))
        if dry:
            continue

        # Get latest rev, if not already added, add it.
        if 'changeset_revision' not in tool:
            tool['changeset_revision'] = []

        if revs[0] not in tool['changeset_revision']:
            # TS doesn't support utf8 and we don't want to either.
            tool['changeset_revision'].append(revs[0].encode('ascii'))

    with open(fn + '.lock', 'w') as handle:
        yaml.dump(locked, handle, default_flow_style=False)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('fn', type=argparse.FileType('r'), help="Tool.yaml file")
    parser.add_argument('--dry-run', action='store_true', help="Trust all listed tools in the file, i.e. add the latest changest for them.")
    args = parser.parse_args()
    update_file(args.fn, dry=args.dry_run)
