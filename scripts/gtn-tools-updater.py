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

# Path to usegalaxy-eu-tools directory
eu_tools_dir = sys.argv[4]

# Merge all yaml.lock files in usegalaxy-eu-tools to determine tool panel label
tools_mix = []
for tool_yaml in glob.glob(f"{eu_tools_dir}/*.yaml.lock"):
    parsed_yaml = yaml.safe_load(open(tool_yaml))
    if 'tools' in parsed_yaml:
        for tool in parsed_yaml['tools']:
            tools_mix.append(tool)


# IUC and mix lookup
def tool_exists (name, topic):
    # Use tool panel name from tools_iuc.yaml.lock when tools are already installed
    for tool in tools_iuc['tools']:
        if tool['name'] == name:
            if 'tool_panel_section_label' in tool:
                return tool['tool_panel_section_label']
    for tool in tools_mix:
        if tool['name'] == name:
            if 'tool_panel_section_label' in tool:
                return tool['tool_panel_section_label']
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
