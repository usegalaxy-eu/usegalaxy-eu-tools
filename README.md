# UseGalaxy tools

There are a couple separate lists of tools contained here. The sum total of them make up the set of tools installed in UseGalaxy.eu


File                                  | Tools
------------------------------------- | -----------
[asaim](./asaim.yaml)                 |
[epigenetics](./epigenetics.yaml)     |
[graphclust](./graphclust.yaml)       |
[metabolomics](./metabolomics.yaml)   |
[tools_galaxyp](./tools_galaxyp.yaml) | Proteomics Tools
[tools_iuc](./tools_iuc.yaml)         | Most of the tools maintained by IUC. We aren't currently planning on automatically adding all the tools from IUC but we may reconsider this later.
[tools](./tools.yaml)                 | Tools not contained in one of the other files.


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
