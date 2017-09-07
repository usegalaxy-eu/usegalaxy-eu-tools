#!/usr/bin/env python
import yaml
import sys
import glob
import logging
logging.basicConfig()
log = logging.getLogger()


sections = open('scripts/sections.tsv', 'r').read().strip().split('\n')
sections = [x.split('\t') for x in sections]
section_list = [x[0] for x in sections] + [x[1] for x in sections]

exit_code = 0
for file in glob.glob("*.yaml"):
    with open(file, 'r') as handle:
        w = yaml.load(handle)

    for tool in w['tools']:

        if 'tool_panel_section_label' not in tool:
            exit_code = 1
            log.error("[%s] Tool %s %s missing section", file, tool['owner'], tool['name'])
            continue

        if tool['tool_panel_section_label'] not in section_list:
            exit_code = 1
            log.error("[%s] Tool %s %s unknown section (%s)", file, tool['owner'], tool['name'], tool['tool_panel_section_label'])

sys.exit(exit_code)
