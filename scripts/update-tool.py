import yaml
import os
import glob
import copy
import argparse

from bioblend import toolshed


ts = toolshed.ToolShedInstance(url='https://toolshed.g2.bx.psu.edu')


def update_file(fn, owner=None, name=None, without=False):
    with open(fn + '.lock', 'r') as handle:
        locked = yaml.load(handle)

    # Update any locked tools.
    for tool in locked['tools']:
        # If without, then if it is lacking, we should exec.
        if without:
            if 'changeset_revision' in tool:
                continue

        if not without and owner and tool['owner'] != owner:
            continue

        if not without and name and tool['name'] != name:
            continue

        try:
            revs = ts.repositories.get_ordered_installable_revisions(tool['name'], tool['owner'])
        except Exception as e:
            print(e)
            continue

        print("Found newer revision of %s/%s (%s)" % (tool['owner'], tool['name'], revs[0]))

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
    parser.add_argument('--owner', help="Repository owner to filter on, anything matching this will be updated")
    parser.add_argument('--name', help="Repository name to filter on, anything matching this will be updated")
    parser.add_argument('--without', action='store_true', help="If supplied will ignore any owner/name and just automatically add the latest hash for anything lacking one.")
    args = parser.parse_args()
    update_file(args.fn.name, owner=args.owner, name=args.name, without=args.without)
