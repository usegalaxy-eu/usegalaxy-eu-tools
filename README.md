# UseGalaxy tools

There are a couple separate lists of tools contained here. The sum total of them make up the set of tools installed in UseGalaxy.eu

## Installation

```console
export PATH=/usr/local/tools/_conda/bin/:$PATH
source activate ephemeris
shed-tools install -t tools.yaml -a $GALAXY_API_KEY --galaxy https://galaxy.uni-freiburg.de
```

## Install of a Single Tool

```console
shed-tools install -a $GALAXY_API_KEY --galaxy https://galaxy.uni-freiburg.de --name annotatemyids --owner iuc --section_label 'Annotation'
```
