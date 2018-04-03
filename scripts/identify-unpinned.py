import yaml
import os
import sys
import argparse


def update_file(fn):
    # If a lock file exists, load it from that file
    with open(fn + '.lock', 'r') as handle:
        locked = yaml.load(handle)

    exit_code = 0
    # As here we add any new tools in.
    unpinned = []
    for tool in locked['tools']:
        if 'revisions' not in tool:
            exit_code = 1
            unpinned.append(tool)

    if len(unpinned) > 0:
        print("Unpinned tools in %s:" % fn)
        for tool in unpinned:
            print("  %s/%s" % (tool['owner'], tool['name']))

    sys.exit(exit_code)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('fn', type=argparse.FileType('r'), help="Tool.yaml file")
    args = parser.parse_args()
    update_file(args.fn.name)
