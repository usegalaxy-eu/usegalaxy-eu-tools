# Galaxy FR tools
List of tools included in the Galaxy Freiburg instance


### Actiavte Conda environment with ephemeris
```
export PATH=/usr/local/tools/_conda/bin/:$PATH
source activate ephemeris
```

### Install/Update all tools specified in tools.yaml
```bash
shed-tools install -t tools.yaml -a $GALAXY_API_KEY --galaxy https://galaxy.uni-freiburg.de
```

### Install a single tool
```bash
shed-tools install -a $GALAXY_API_KEY --galaxy https://galaxy.uni-freiburg.de --name annotatemyids --owner iuc --section_label 'Annotation'
```

