#!/usr/bin/env python

# Execute this script in the root directory of GTN `python bin/allgtntoolsyaml.py`
# Dependency: Ephemeris

import glob
import yaml
import os
import sys

t = open(sys.argv[2], "w")

baseyaml = { 'install_tool_dependencies': True, 'install_repository_dependencies': True, 'install_resolver_dependencies': True , 'tools':[]}

def toolyamltodict (yamlfile, baseyaml, topic):
    for i, tool in enumerate(yamlfile['tools']):
        yamlfile['tools'][i]['tool_panel_section_label'] = topic
        baseyaml['tools'].append(tool)
    return baseyaml

topicslist = [f.name for f in os.scandir(f"{sys.argv[1]}/topics/") if f.is_dir()]
topicslist.sort()

for topic in topicslist:
    for tutorial in [s.name for s in os.scandir("./topics/{}/tutorials".format(topic)) if s.is_dir()]:

        toolpath = "./topics/{}/tutorials/{}/tools.yaml".format(topic,tutorial)
        workflowpath = "./topics/{}/tutorials/{}/workflows".format(topic,tutorial)

        if os.path.exists(workflowpath) and glob.glob("{}/*.ga".format(workflowpath)):
            for nr, workflow in enumerate(glob.glob("{}/*.ga".format(workflowpath))):
                os.system("workflow-to-tools -w {} -o {}/temp_tool_{}.yaml".format(workflow,workflowpath,nr))
                worktools = yaml.load(open("{}/temp_tool_{}.yaml".format(workflowpath,nr)))
                baseyaml = toolyamltodict(worktools, baseyaml, topic.title())
                os.remove("{}/temp_tool_{}.yaml".format(workflowpath,nr))



yaml.dump(baseyaml, t, default_flow_style=False)

t.close()