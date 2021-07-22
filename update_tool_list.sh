#!/bin/bash
set -e
. ~/.bashrc

if git remote -v | egrep -q 'https://github.com/usegalaxy-eu/usegalaxy-eu-tools.git'; then
    echo "upstream repository is already set to usegalaxy-eu-tools"
else
    echo "setting upstream repository to usegalaxy-eu-tools"
    git remote add upstream https://github.com/usegalaxy-eu/usegalaxy-eu-tools.git
fi

git show remotes/upstream/master:tools_iuc.yaml.lock > tmp_tools_iuc_eu.yaml.lock

if cmp --silent -- "tmp_tools_iuc_eu.yaml.lock" "tools_iuc_eu.yaml.lock"; then
  echo "tools_iuc_eu.yaml.lock has not been updated on usegalaxy-eu-tools"
  rm tmp_tools_iuc_eu.yaml.lock
else
  echo "tools_iuc_eu.yaml.lock has been updated on usegalaxy-eu-tools"
  rm tools_iuc_eu.yaml.lock
  mv tmp_tools_iuc_eu.yaml.lock tools_iuc_eu.yaml.lock
  process_yaml.py --revision_only --base_file tools_iuc.yaml.lock --tools_yaml tools_iuc_eu.yaml.lock -o merge_updated.yaml.lock
fi
