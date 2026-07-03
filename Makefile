YAML_FILES := $(wildcard *.yaml)
LOCK_FILES := $(wildcard *.yaml.lock)
LINTED_YAMLS := $(YAML_FILES:=.lint)
UPDATED_YAMLS := $(YAML_FILES:=.update)
CORRECT_YAMLS := $(YAML_FILES:=.fix)
INSTALL_YAMLS := $(LOCK_FILES:=.install)
UPDATE_TRUSTED_IUC := $(LOCK_FILES:.lock=.update_trusted_iuc)
DEPRECATED_YAMLS := $(LOCK_FILES:=.deprecate)

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
	@-shed-tools install --toolsfile $< --galaxy $(GALAXY_SERVER) --api_key $(GALAXY_API_KEY) 2>&1 | tee -a report.log

pr_check:
	for changed_yaml in `git diff remotes/origin/master --name-only | grep '.yaml$$' | grep -v '.not-installable-revisions.yaml$$'`; do python scripts/pr-check.py $${changed_yaml} && pykwalify -d $${changed_yaml} -s .schema.yaml ; done

update_trusted: $(UPDATE_TRUSTED_IUC) ## Run the update script
	@# Missing --without, so this updates all tools in the selected files in one process.
	python3 scripts/update-tool.py cheminformatics.yaml imaging.yaml tools_iuc.yaml earlhaminst.yaml rnateam.yaml bgruening.yaml ecology.yaml tools_galaxyp.yaml single-cell-ebi-gxa.yaml genome-annotation.yaml galaxy-australia.yaml climate.yaml nml.yaml peterjc.yaml goeckslab.yaml eirene.yaml lldelisle.yaml tools_q2d2.yaml ufz.yaml

update_all: $(UPDATED_YAMLS)

%.update: ## Update all of the tools
	@# Missing --without, so this updates all tools in the file.
	python3 scripts/update-tool.py $<

%.update_trusted_iuc: %
	@# Update any tools owned by IUC in any other yaml file
	python3 scripts/update-tool.py --owner iuc $<

update: ## Add new tools' revisions: fix lockfiles, lint, then update trusted tools (stages run sequentially)
	$(MAKE) fix -j $$(nproc)
	$(MAKE) lint -j $$(nproc)
	$(MAKE) update_trusted -j $$(nproc)

# Optional overrides for syncing a single source repo (used by the per-repo sync-tools
# workflow, which needs its own gating/PR/report per target). When NAME/REPO/YAML are
# all set (as make vars or env vars), only that one target is synced; otherwise every
# entry in SYNC_TARGETS runs. `?=` so values passed via the environment (e.g. from a
# GitHub Actions `env:` block) aren't clobbered by these defaults.
SYNC_CATCHUP ?=
SYNC_REPORT_FILE ?=

sync: ## Sync new tools from upstream source repos (expects ./$(NAME) checkouts, see scripts/sync-targets.json), or a single one via NAME=/REPO=/YAML=
ifneq ($(strip $(NAME)$(REPO)$(YAML)),)
	@if [ ! -d "$(NAME)" ]; then \
		echo "==> Cloning $(REPO) into ./$(NAME)"; \
		git clone --quiet --filter=blob:none "https://github.com/$(REPO).git" "$(NAME)"; \
	fi
	python3 scripts/sync-tools-repo.py \
		--tools-yaml $(YAML) \
		--mapping-file scripts/category-mapping.yml \
		--source-repo-path $(NAME) \
		--source-repo-url https://github.com/$(REPO) \
		--github-token "$$GITHUB_TOKEN" \
		--last-sync-sha-file scripts/.last-$(NAME)-sync-sha \
		--skip-list scripts/sync-skipped-tools.yml \
		--skip-list-key $(NAME) \
		$(if $(SYNC_REPORT_FILE),--report-file $(SYNC_REPORT_FILE)) \
		$(if $(filter true,$(SYNC_CATCHUP)),--catchup)
else
	@jq -r '.[] | "\(.name)\t\(.source_repo)\t\(.tools_yaml)"' scripts/sync-targets.json | while IFS=$$(printf '\t') read -r name repo yaml; do \
		echo "==> Syncing $$name from $$repo into $$yaml"; \
		$(MAKE) sync NAME=$$name REPO=$$repo YAML=$$yaml || exit 1; \
	done
endif

deprecate: $(DEPRECATED_YAMLS) ## Remove not-installable revisions from all lock files

%.deprecate: %
	python3 scripts/fix_outdated.py $<


.PHONY: pr_check lint update_trusted update sync deprecate help
