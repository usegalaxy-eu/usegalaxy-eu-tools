import yaml
import sys
import argparse
import copy
import os

# Small script that syncs a yaml and yaml.lock file

lock_file = open("/home/padge/Elixir/galaxy-tool-development/usegalaxy-be-tools/tools_iuc.yaml.lock","r")
lock_yaml = yaml.safe_load(lock_file)
len(lock_yaml['tools'])
l = [x['name'] for x in lock_yaml['tools']]
set([x for x in l if l.count(x) > 1])

tools_file = open("/home/padge/Elixir/galaxy-tool-development/usegalaxy-be-tools/tools_iuc.yaml","r")
tools_yaml = yaml.safe_load(tools_file)
tools_yaml['tools'][0].keys()
tools_yaml.keys()



synced_tools_yaml = copy.deepcopy(tools_yaml)

unique_tools = {x['name']:x for x in tools_yaml['tools']}
updated_unique_tools = copy.deepcopy(unique_tools)
unique_lock_tools = {x['name']:x for x in lock_yaml['tools']}

i=0
j=0
for k in unique_lock_tools.keys():
    if not k in unique_tools.keys():
        tmp = unique_lock_tools[k]
        print({key: tmp[key] for key in tmp if key != 'revisions'})
        updated_unique_tools[k] = {key: tmp[key]
                                   for key in tmp if key != 'revisions'}
        # print(unique_lock_tools[k])
        i+=1
    else:
        j+=1

print(i)
print(j)
print(len(unique_tools))
print(len(unique_lock_tools))
print(len(updated_unique_tools.values()))

synced_tools_yaml['tools'] = list(updated_unique_tools.values())

len(synced_tools_yaml['tools'])

{key: synced_tools_yaml[key]
    for key in synced_tools_yaml if key != 'tools'}

out_file = "/home/padge/Elixir/galaxy-tool-development/usegalaxy-be-tools/tools_iuc.yaml"
with open(out_file, 'w') as outfile:
    yaml.dump(synced_tools_yaml, outfile,
              default_flow_style=False, explicit_start=True)
