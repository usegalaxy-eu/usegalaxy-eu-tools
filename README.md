# usegalaxy.\* tools [![Build Status](https://build.galaxyproject.eu/buildStatus/icon?style=flat-square&subject=Update%20Trusted&job=usegalaxy-eu%2Fupdate-trusted-tools)](https://build.galaxyproject.eu/job/usegalaxy-eu/job/update-trusted-tools/) [![Build Status](https://build.galaxyproject.eu/buildStatus/icon?style=flat-square&subject=Install%20Tools&job=usegalaxy-eu%2Finstall-tools)](https://build.galaxyproject.eu/job/usegalaxy-eu/job/install-tools/)


Originally this repository was solely for the use of usegalaxy.eu, but we are looking at expanding that to the other usegalaxy.\* instances.
Some documentation may be outdated while we figure out the new policies and procedures.

Currently only UseGalaxy.eu is installing tools from this repository.

All installed tools are also listed on our [webpage](https://galaxyproject.eu/tools).

## Usage

With [ephemeris](https://ephemeris.readthedocs.io/en/latest/) installed, you can use our tool defintions easily:

```bash
make tools_iuc.yaml.lock.install GALAXY_SERVER_URL=https://... GALAXY_API_KEY=...
```

## Setup

- `yaml` files are manually curated
- `yaml.lock` files are automatically generated
- Only IUC tools are automatically updated with the latest version each week

## Requesting Tools in UseGalaxy.\*

Policies are not set in stone and we would be happy to seek feedback and discussions.
Currenty, we encourage everyone to submit tools via PRs to this repo. The tools are losely grouped into several categories based on the yaml files. Please make your changes in the appropriate file and avoid creating a new yaml file unless necessary.

However, we promise a high-quality service to
our users and we need to ensure sustainability of the installed tools. That means that tools are regularly updated, tested
and can be adjusted to new developments.
Therefore, we encourage everyone to follow the [IUC Guidelines](https://galaxy-iuc-standards.readthedocs.io/en/latest/index.html) for tool development and have automatic testing enabled via [CI](https://en.wikipedia.org/wiki/Continuous_integration).

We encourage you to submit your tool to one of the larger community repositories, like

 * [Galaxy Tools maintained by IUC](https://github.com/galaxyproject/tools-iuc)
 * [Björn Grüning repo](https://github.com/bgruening/galaxytools)
 * Peter Cock's repos:
   * [pico repo](https://github.com/peterjc/pico_galaxy)
 * [Galaxy Proteomics repo](https://github.com/galaxyproteomics/tools-galaxyp)
 * [EI repo](https://github.com/TGAC/earlham-galaxytools)

 These repositories have planemo CI testing enabled and have a larger communities in place that help you with maintaining the
 tools.

### Updating an Existing Tool

- Edit the .yaml.lock file to add the latest/specific changeset revision for the tool. You can use `python scripts/update-tool.py --owner <repo-owner> --name <repo-name> <file.yaml.lock>` in order to do this if you just want to add the latest revision.
- Open a pull request

### Requesting a New Tool

- If you just want the latest version:
	- Edit the .yaml file to add name/owner/section
- If you want a specific version:
	- Edit the .yaml file to add name/owner/section
	- Run `make fix`
	- Edit the .yaml.lock to correct the version number.
- Open a pull request
