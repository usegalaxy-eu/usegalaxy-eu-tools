import json
with open('tsr.json', 'r') as handle:
    data = json.load(handle)

t = {}
for x in data:
    t[(x['owner'], x['name'])] = x['changeset_revision']


import yaml
import glob
for file in glob.glob("*.yaml"):
    with open(file, 'r') as handle:
        w = yaml.load(handle)

    for tool in w['tools']:
        key = (tool['owner'], tool['name'])
        if key in t:
            tool['changeset_revision'] = str(t[key])
    
    with open(file, 'w') as handle:
        yaml.dump(w, handle, default_flow_style=False)
