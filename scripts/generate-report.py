#!/usr/bin/env python
import sys
import os
import datetime

today = datetime.date.today()

sections = {}

lastTool = None
for line in sys.stdin:
    # strip newline
    line = line.strip()

    # If it's a tool install, record tool name
    if line.startswith('(') and 'Installing repository' in line:
        q = line.split()

        repo = q[3]
        owner = q[5]
        section = line[line.index('"') + 1:line.rindex('"')]
        revision = q[q.index('revision') + 1]

        if section not in sections:
            sections[section] = []

        sections[section].append((owner, repo, revision))


print("""
---
site: freiburg
tags: [tools]
title: UseGalaxy.eu Tool Updates for {date}
supporters:
- denbi
- elixir
---

# Tool Updates

On {date}, the tools on UseGalaxy.eu were updated by our automated tool update and installation process in [Jenkins Build #{build_number}](https://build.galaxyproject.eu/job/usegalaxy-eu/job/install-tools/#{build_number}/)

""".format(date=today, build_number=os.environ.get('BUILD_NUMBER', '??')))

for section in sections:
    print("## {}\n".format(section))
    for (owner, repo, revision) in sorted(set(sections[section])):
        print("- {repo} was updated to [{revision}](https://toolshed.g2.bx.psu.edu/view/{owner}/{repo}/{revision})".format(**locals()))
    print('')
