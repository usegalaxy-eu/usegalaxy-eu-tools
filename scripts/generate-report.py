#!/usr/bin/env python
import sys
import os
import datetime

today = datetime.date.today()

sections = {}

lastTool = None
installing_repo = False
for line in sys.stdin:
    # strip newline
    line = line.strip()
    # If it's a tool install, record tool name
    if line.startswith('(') and 'Installing repository' in line:
        # new installation begins
        installing_repo = True
        q = line.split()
        repo = q[3]
        owner = q[5]
        section = line[line.index('"') + 1:line.rindex('"')]
        revision = q[q.index('revision') + 1]

    elif installing_repo and "is already installed." not in line:
        # installing_repo was tracked and it was not already installed, so this is a true positive one
        if section not in sections:
            sections[section] = []
        sections[section].append((owner, repo, revision))
        installing_repo = False
    elif installing_repo and not line.startswith('('):
        # We have been tracking a repo install, but nothing was installed. False positive.
        # This happens when 'is already installed.' is part of the line string.
        installing_repo = False
    elif "installed successfully" in line:
        # installation is finished
        installing_repo = False

if not sections:
    sys.exit(0)

print("""---
site: freiburg
tags: [tools]
title: UseGalaxy.eu Tool Updates for {date}
supporters:
- denbi
- elixir
---

On {date}, the tools on UseGalaxy.eu were updated by our automated tool update and installation process in [Jenkins Build #{build_number}](https://build.galaxyproject.eu/job/usegalaxy-eu/job/install-tools/#{build_number}/)

""".format(date=today, build_number=os.environ.get('BUILD_NUMBER', '??')))

for section in sections:
    print("## {}\n".format(section))
    for (owner, repo, revision) in sorted(set(sections[section])):
        print("- {repo} was updated to [{revision}](https://toolshed.g2.bx.psu.edu/view/{owner}/{repo}/{revision})".format(**locals()))
    print('')
