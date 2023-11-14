#!/usr/bin/env python
import glob
import yaml
import json
import os

data = {}
for fn in sorted(glob.glob("*.yaml")):
    with open(fn, 'r') as handle:
        tools = yaml.safe_load(handle)
        for x in tools['tools']:
            if 'tool_panel_section_label' in x:
                data[f"{x['owner']}/{x['name']}"] = x['tool_panel_section_label']

os.makedirs('api/', exist_ok=True)
with open('api/labels.json', 'w') as handle:
    json.dump(data, handle)
