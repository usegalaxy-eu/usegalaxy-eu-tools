# usegalaxy.\* tools

Originally this repository was solely for the use of usegalaxy.eu, but we are looking at expanding that to the other usegalaxy.\* instances. Some documentation may be outdated while we figure out the new policies and procedures.

Currently only UseGalaxy.eu is installing tools from this repository.

## Setup

- `yaml` files are manually curated
- `yaml.lock` files are automatically generated
- Only IUC tools are automatically updated with the latest version each week

## Requesting Tools in UseGalaxy.\*

Policies are not yet announced.

The tools are losely grouped into several categories based on the yaml files. Please make your changes in the appropriate file and avoid creating a new yaml file unless necessary.

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

## For UseGalaxy.\* Instance Administrators

Set the environment variables `GALAXY_SERVER_URL` and `GALAXY_API_KEY` and run `make install`. This will install ALL of the tools from the .lock files. Be sure that the tool panel sections are pre-existing or it will make a mess of your tool panel. You can run `grep -o -h 'tool_panel_section_label:.*' *.yaml.lock | sort -u` for a list of categories.

## On UseGalaxy.eu

Currently, UseGalaxy.eu runs this on our Jenkins server. Every saturday morning it wakes up early and updates all IUC owned tools + ensures that all the yaml files are installed to usegalaxy.eu.
