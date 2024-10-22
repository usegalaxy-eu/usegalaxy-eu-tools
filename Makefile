YAML_FILES := $(wildcard *.yaml)
LOCK_FILES := $(wildcard *.yaml.lock)
LINTED_YAMLS := $(YAML_FILES:=.lint)
UPDATED_YAMLS := $(YAML_FILES:=.update)
CORRECT_YAMLS := $(YAML_FILES:=.fix)
INSTALL_YAMLS := $(LOCK_FILES:=.install)
UPDATE_TRUSTED_IUC := $(LOCK_FILES:.lock=.update_trusted_iuc)

GALAXY_SERVER := https://usegalaxy.eu


help:
	@egrep '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

lint: $(LINTED_YAMLS) ## Lint the yaml files
fix: $(CORRECT_YAMLS) ## Fix any issues (missing hashes, missing lockfiles, etc.)
install: $(INSTALL_YAMLS) ## Install the tools in our galaxy

%.lint: %
	python3 scripts/fix-lockfile.py $<
	pykwalify -d $< -s .schema.yaml
	python3 scripts/identify-unpinned.py $<

%.fix: %
	@# Generates the lockfile or updates it if it is missing tools
	python3 scripts/fix-lockfile.py $<
	@# --without says only add those hashes for those missing hashes (i.e. new tools)
	python3 scripts/update-tool.py $< --without

%.install: %
	@echo "Installing any updated versions of $<"
	@-shed-tools install --install_resolver_dependencies --toolsfile $< --galaxy $(GALAXY_SERVER) --api_key $(GALAXY_API_KEY) 2>&1 | tee -a report.log

pr_check:
	for changed_yaml in `git diff remotes/origin/master --name-only | grep .yaml$$`; do python scripts/pr-check.py $${changed_yaml} && pykwalify -d $${changed_yaml} -s .schema.yaml ; done

update_trusted: $(UPDATE_TRUSTED_IUC) ## Run the update script
	@# Missing --without, so this updates all tools in the file.
	python3 scripts/update-tool.py cheminformatics.yaml
	python3 scripts/update-tool.py imaging.yaml
	python3 scripts/update-tool.py tools_iuc.yaml
	python3 scripts/update-tool.py earlhaminst.yaml
	python3 scripts/update-tool.py rnateam.yaml
	python3 scripts/update-tool.py bgruening.yaml
	python3 scripts/update-tool.py ecology.yaml
	python3 scripts/update-tool.py tools_galaxyp.yaml
	python3 scripts/update-tool.py single-cell-ebi-gxa.yaml
	python3 scripts/update-tool.py genome-annotation.yaml
	python3 scripts/update-tool.py galaxy-australia.yaml
	python3 scripts/update-tool.py climate.yaml
	python3 scripts/update-tool.py nml.yaml
	python3 scripts/update-tool.py peterjc.yaml
	python3 scripts/update-tool.py goeckslab.yaml
	python3 scripts/update-tool.py eirene.yaml
	python3 scripts/update-tool.py lldelisle.yaml
	python3 scripts/update-tool.py tools_q2d2.yaml
	python3 scripts/update-tool.py ufz.yaml

update_all: $(UPDATED_YAMLS)

%.update: ## Update all of the tools
	@# Missing --without, so this updates all tools in the file.
	python3 scripts/update-tool.py $<

%.update_trusted_iuc: %
	@# Update any tools owned by IUC in any other yaml file
	python3 scripts/update-tool.py --owner iuc $<


.PHONY: pr_check lint update_trusted help
