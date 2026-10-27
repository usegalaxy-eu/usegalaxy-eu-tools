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

## Why tools should come from trusted community repositories

Tools installed on the usegalaxy.\* instances should ideally originate from trusted community repositories.
Such repositories provide several advantages over individual, self-published tool wrappers:

- **CI-tested tools**: Every proposed change is automatically linted and tested with [planemo](https://planemo.readthedocs.io) via continuous integration, ensuring that only functional, high-quality wrappers reach the Tool Shed and, ultimately, our servers.
- **Community review to secure tools and enhance UX**: Wrappers are reviewed by experienced community members before they are merged. This review process checks tools for security issues before deployment and improves the user experience of the tool interface. If the component tools are trusted, workflows built from them can likewise be trusted.
- **Automatic container generation (Docker, Singularity)**: The automated update pipeline connecting upstream software releases, Bioconda, BioContainers, and Galaxy tool wrappers ensures that Docker and Singularity containers are built automatically for every new tool version. This is described in the Planemo paper: Bray et al., *The Planemo toolkit for developing, deploying, and executing scientific data analyses in Galaxy and beyond*, Genome Research 33(2), 261–268 (2023), [doi:10.1101/gr.276963.122](https://doi.org/10.1101/gr.276963.122).
- **Automatic tool updates in this repository**: Tools from the trusted repositories listed below are automatically updated in this repository with the latest version each week (currently only IUC tools), keeping the installed tool set up to date with little manual effort.

## Requesting Tools in UseGalaxy.\*

Policies are not set in stone and we would be happy to seek feedback and discussions.
Currenty, we encourage everyone to submit tools via PRs to this repo. The tools are losely grouped into several categories based on the yaml files. Please make your changes in the appropriate file and avoid creating a new yaml file unless necessary.

However, we promise a high-quality service to
our users and we need to ensure sustainability of the installed tools. That means that tools are regularly updated, tested
and can be adjusted to new developments.
Therefore, we encourage everyone to follow the [IUC Guidelines](https://galaxy-iuc-standards.readthedocs.io/en/latest/index.html) for tool development and have automatic testing enabled via [CI](https://en.wikipedia.org/wiki/Continuous_integration).

We encourage you to submit your tool to one of the trusted community repositories listed below. These repositories have planemo CI testing enabled and have a larger communities in place that help you with maintaining the tools. The right-hand column shows the tool list(s) in this repository that track tools from each repository.

| Trusted community repository | Tool lists in this repository |
| --- | --- |
| [Galaxy Tools maintained by IUC](https://github.com/galaxyproject/tools-iuc) | `tools_iuc.yaml` |
| [Galaxy EU repo](https://github.com/bgruening/galaxytools) | `bgruening.yaml` |
| [Galaxy Proteomics repo](https://github.com/galaxyproteomics/tools-galaxyp) | `tools_galaxyp.yaml` |
| [EI repo](https://github.com/TGAC/earlham-galaxytools) | `earlhaminst.yaml` |
| [RECETOX repo](https://github.com/RECETOX/galaxytools) | `eirene.yaml` |
| [Workflow4metabolomics repo](https://github.com/workflow4metabolomics/galaxy_codex) | `metabolomics.yaml` |
| [Muon Spectroscopy Computational Project repo](https://github.com/muon-spectroscopy-computational-project/muon-galaxy-tools) | `materials.yaml` |
| [Earth Data Community repo](https://github.com/earth-data-community/galaxy-tools) | `ecology.yaml` |
| [Ecology repo](https://github.com/galaxyecology/tools-ecology) | `ecology.yaml` |


### Updating an Existing Tool

- Edit the .yaml.lock file to add the latest/specific changeset revision for the tool. You can use `python scripts/update-tool.py --owner <repo-owner> --name <repo-name> <file.yaml>` in order to do this if you just want to add the latest revision.
- Open a pull request

### Requesting a New Tool

- If you just want the latest version:
	- Edit the .yaml file to add name/owner/section
- If you want a specific version:
	- Edit the .yaml file to add name/owner/section
	- Run `make fix`
	- Edit the .yaml.lock to correct the version number.
- Open a pull request
