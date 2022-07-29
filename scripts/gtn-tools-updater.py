#!/usr/bin/env python

# Dependency: Ephemeris

import glob
import yaml
import os
import sys

# Path to output yaml file
output_file = sys.argv[2]

# Path to tools_iuc.yaml.lock 
tools_iuc = yaml.safe_load(open(sys.argv[3]))

# Path to mapping file directory
mapping_file = yaml.safe_load(open(sys.argv[4]))

# IUC and mapping lookup
def tool_exists (name, topic):
    # Use tool panel name from tools_iuc.yaml.lock when tools are already installed
    for tool in tools_iuc['tools']:
        if tool['name'] == name:
            if 'tool_panel_section_label' in tool:
                return tool['tool_panel_section_label']

    # if tool is in mapping file, use panel section label from mapping
    for section, tools in mapping_file['tool_mapping'].items():
        if name in tools:
            return section

    # If section is mapping file, use renamed section from mapping file
    if topic.title() in mapping_file['section_mapping']:
        return mapping_file['section_mapping'][topic.title()]
    else:
        return topic.title()

# Tool parsing
def toolyamltodict (yamlfile, baseyaml, topic):
    for i, tool in enumerate(yamlfile['tools']):
        yamlfile['tools'][i]['tool_panel_section_label'] = tool_exists(yamlfile['tools'][i]['name'], topic)
        baseyaml['tools'].append(tool)
    return baseyaml


with open(output_file, "w") as f:

    baseyaml = { 'install_tool_dependencies': False, 'install_repository_dependencies': True, 'install_resolver_dependencies': True , 'tools':[]}

    # Determine topics
    topicslist = [f.name for f in os.scandir(f"{sys.argv[1]}/topics/") if f.is_dir()]
    topicslist.sort()

    # Generating the tool files and parse them for each workflow
    for topic in topicslist:
        print(f"\nParsing..... {topic}")
        topic_path = f"{sys.argv[1]}/topics/{topic}"
        for tutorial in [s.name for s in os.scandir(f"{topic_path}/tutorials") if s.is_dir()]:
            print("- " + tutorial)
            toolpath = f"{topic_path}/tutorials/{tutorial}/tools.yaml"
            workflowpath = f"{topic_path}/tutorials/{tutorial}/workflows"

            if os.path.exists(workflowpath) and glob.glob(f"{workflowpath}/*.ga"):
                for nr, workflow in enumerate(glob.glob(f"{workflowpath}/*.ga")):
                    os.system(f"workflow-to-tools -w {workflow} -o {workflowpath}/temp_tool_{nr}.yaml")
                    worktools = yaml.safe_load(open(f"{workflowpath}/temp_tool_{nr}.yaml"))
                    baseyaml = toolyamltodict(worktools, baseyaml, topic)
                    os.remove(f"{workflowpath}/temp_tool_{nr}.yaml")


    # Dump newly generated dictionary to yaml 
    yaml.dump(baseyaml, f, default_flow_style=False)
