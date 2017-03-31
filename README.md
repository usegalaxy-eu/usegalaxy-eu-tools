# galaxy-fr-tools
List of tools include in Galaxy-FR


### Actiavte Conda environment with ephemeris
```
export PATH=/usr/local/tools/_conda/bin/:$PATH
source activate ephemeris
```

### Install/Update all tools specified in tools.yaml

shed-install -t tools.yaml -a $GALAXY_API_KEY 

### Install a single tool

shed-install --name prokka --owner crs4 --section_label 'Annotation' -a $GALAXY_API_KEY


