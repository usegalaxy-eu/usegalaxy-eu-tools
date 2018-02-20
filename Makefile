YAML_FILES := $(wildcard *.yaml)
LINTED_YAMLS := $(YAML_FILES:=.lint)
CORRECT_YAMLS := $(YAML_FILES:=.fix)
INSTALL_YAMLS := $(YAML_FILES:=.install)

GALAXY_SERVER := https://usegalaxy.eu


help:
	@egrep '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

lint: $(LINTED_YAMLS) ## Lint the yaml files
fix: $(CORRECT_YAMLS) ## Fix any issues (missing hashes, missing lockfiles, etc.)
install: $(INSTALL_YAMLS) ## Install the tools in our galaxy

%.lint: %
	pykwalify -d $< -s .schema.yaml
	python scripts/identify-unpinned.py $<

%.fix: %
	@# Generates the lockfile or updates it if it is missing tools
	python scripts/fix-lockfile.py $<
	@# --without says only add those hashes for those missing hashes (zB new tools)
	python scripts/update-tool.py $< --without

%.install: %
	@echo "Installing any updated versions of $<"
	@shed-tools install --toolsfile $< --galaxy $(GALAXY_SERVER) --api_key $(GALAXY_API_KEY)


update_trusted: ## Run the update script
	@# Missing --without, so this updates all tools in the file.
	python scripts/update-tool.py tools_iuc.yaml

.PHONY: lint update_trusted help
