import yaml
import os
import glob
import copy

from bioblend import toolshed


ts = toolshed.ToolShedInstance(url='https://toolshed.g2.bx.psu.edu')
TRUSTED_AUTHORS = (
    'iuc',
)

TRUSTED_REPOSITORIES = (
    # (owner, repo_name)
)

for file in glob.glob("*.yaml"):
    print("Processing %s" % file)

    # Load the main tool list containing just the owner/repo name
    with open(file, 'r') as handle:
        unlocked = yaml.load(handle)
    # If a lock file exists, load it from that file
    if os.path.exists(file + '.lock'):
        with open(file + '.lock', 'r') as handle:
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
        # if the tool is trusted, update it.
        if tool['owner'] in TRUSTED_AUTHORS or (tool['owner'], tool['name']) in TRUSTED_REPOSITORIES:
            # get CR
            try:
                revs = ts.repositories.get_ordered_installable_revisions(tool['name'], tool['owner'])
            except Exception as e:
                print(e)
                continue
            # Get latest rev, if not already added, add it.
            if 'changeset_revision' in tool:
                if revs[0] not in tool['changeset_revision']:
                    tool['changeset_revision'].append(revs[0])
                    print("  Found newer revision of %s/%s (%s)" % (tool['owner'], tool['name'], revs[0]))
            else:
                tool['changeset_revision'] = [revs[0]]
                print("  Found newer revision of %s/%s (%s)" % (tool['owner'], tool['name'], revs[0]))

    with open(file + '.lock', 'w') as handle:
        yaml.dump(locked, handle, default_flow_style=False)
