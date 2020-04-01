# usegalaxy.be tools

This repository contains the lists of tools installed in usegalaxy.be.
The tools installed are basically split in 3 lists:
- tools_iuc.yaml updated from upstream usegalaxy.\* repo (https://github.com/usegalaxy-eu/usegalaxy-eu-tools)
- belgium-custom.yaml listing tools installed only in usegalaxy.be.
- GTN_tutorials_tools.yaml listing tools from the [Galaxy Training Network](https://github.com/galaxyproject/training-material). This list is based on GTN release [2020-04-01](https://github.com/galaxyproject/training-material/releases/tag/2020-04-01).

Tools are included initially in the belgium-custom list and, if the tool meets the requirements, a request is made and it is later included upstream in the tools_iuc.



## Requesting Tools in usegalaxy.be

Following the previous description, the options to get a tool included in usegalaxy.be are 2:

- Follow the procedure to add it to tools_iuc list in https://github.com/usegalaxy-eu/usegalaxy-eu-tools
- Make a pull request to add it in belgium-custom.yaml list in this repository. 

For the second option the options are:


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

Always stick to the section names in tool_conf.xml

## For UseGalaxy.\* Instance Administrators

Set the environment variables `GALAXY_SERVER_URL` and `GALAXY_API_KEY` and run `make install`. This will install ALL of the tools from the .lock files. Be sure that the tool panel sections are pre-defined in the the tool_conf.xml or this can create a mess in your tool panel. You can run `grep -o -h 'tool_panel_section_label:.*' *.yaml.lock | sort -u` for a list of categories.

By default the value install_resolver_dependencies is set to True when running shed-tools install through Ephemeris. If preferred, this can be set to false to install the wrapper and Galaxy dependencies only. The resolver dependencies (e.g conda) can be installed later using Ephemeris (function install-tool-deps), Bioblend, or wait for them to be installed automatically at runtime. This is useful if you want to provide a large set of tools but most of them won't be used in the short term.
 
