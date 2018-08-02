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


## Updating a Tool

We have written a small script to help you in requesting updates to specific tools.


```
python scripts/update-tool.py --owner iuc metabolomics.yaml
```

Will look through every tool in metabolomics.yaml, check if it is owned by IUC,
and if it is, it will fetch the latest versions of that tool. If the latest
version has not been seen before, it will be added to the .lock file. Jenkins
will later install these versions automatically.

## Installation (Automatic)

Is completely automated and runs on our Jenkins server. Every saturday morning
it wakes up early and updates all IUC owned tools + ensures that all the yaml
files are installed to usegalaxy.eu.

## Installation (Manual)

```console
export PATH=/usr/local/tools/_conda/bin/:$PATH
source activate ephemeris
shed-tools install -a $GALAXY_API_KEY --galaxy https://galaxy.uni-freiburg.de -t tools.yaml
```

Or for a single tool

```console
shed-tools install -a $GALAXY_API_KEY --galaxy https://galaxy.uni-freiburg.de --name annotatemyids --owner iuc --section_label 'Annotation'
```
