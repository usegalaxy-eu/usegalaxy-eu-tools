#!/bin/bash
set -e

. ~/.bashrc
export PATH=/usr/local/tools/_conda/bin/:$PATH
source activate ephemeris

shed-install -t tools_iuc.yaml -a $GALAXY_API_KEY --galaxy https://galaxy.uni-freiburg.de
shed-install -t tools_galaxyp.yaml -a $GALAXY_API_KEY --galaxy https://galaxy.uni-freiburg.de


/usr/local/galaxy/galaxy-fr-tools/fix_conda_env.sh
