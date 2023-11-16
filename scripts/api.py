#!/usr/bin/env python
import glob
import yaml
import json
import os
import sys

disambig = {}
if len(sys.argv) > 1:
    pref_json_fn = sys.argv[1]
    with open(pref_json_fn, 'r') as f:
        disambig = json.load(f)

data = {}
for fn in sorted(glob.glob("*.yaml")):
    with open(fn, 'r') as handle:
        tools = yaml.safe_load(handle)
        for x in tools['tools']:
            name=f"{x['owner']}/{x['name']}"
            if 'tool_panel_section_label' in x:
                if name in data:
                    if data[name] != x['tool_panel_section_label']:
                        if name in disambig:
                            data[name] = disambig[name]
                        else:
                            print(f"The tool {name} is asigned to {data[name]} but also found in {x['tool_panel_section_label']}")
                else:
                    data[name] = x['tool_panel_section_label']

os.makedirs('api/', exist_ok=True)
with open('api/labels.json', 'w') as handle:
    json.dump(data, handle)
