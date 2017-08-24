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
    #(owner, repo_name)
)

for file in glob.glob("*.yaml"):
    print("Processing %s" % file)
    with open(file, 'r') as handle:
        unlocked = yaml.load(handle)

    if os.path.exists(file + '.lock'):
        with open(file + '.lock', 'r') as handle:
            locked = yaml.load(handle)
    else:
        locked = copy.deepcopy(unlocked)
    locked_tools = [x['name'] for x in locked['tools']]

    # Copy newly added tools to lockfile
    for tool in unlocked['tools']:
        if tool['name'] not in locked_tools:
            locked_tools.append(tool)

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
                    print("  Updating %s %s to %s" % (tool['owner'], tool['name'], revs[0]))
            else:
                tool['changeset_revision'] = [revs[0]]
                print("  Updating %s %s to %s" % (tool['owner'], tool['name'], revs[0]))

    with open(file + '.lock', 'w') as handle:
        yaml.dump(locked, handle, default_flow_style=False)
