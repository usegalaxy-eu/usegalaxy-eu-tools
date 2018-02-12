help:
	@egrep '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-10s\033[0m %s\n", $$1, $$2}'

lint: ## Lint the yaml files
	@# Running process' job to ensure requirements.txt is installed.
	@# I spent 10 minutes reading makefile's manual before concluding it was a list of like 5 files that changes maybe 1/year.
	pykwalify -d asaim.yaml         -s .schema.yaml
	pykwalify -d epigenetics.yaml   -s .schema.yaml
	pykwalify -d graphclust.yaml    -s .schema.yaml
	pykwalify -d metabolomics.yaml  -s .schema.yaml
	pykwalify -d tools_galaxyp.yaml -s .schema.yaml
	pykwalify -d tools_iuc.yaml     -s .schema.yaml
	pykwalify -d tools.yaml         -s .schema.yaml

update_trusted: ## Run the update script + COMMIT THE RESULT
	@# Again, could be made into a fancy target but since this should be run due to changes in remote system, we're doing it the KISS way.
	python scripts/update-trusted.py tools_iuc.yaml
	git config user.email "admin@usegalaxy.eu"
	git config user.name "usegalaxy.eu bot"
	git config push.default current
	git add *.lock
	git commit -m "Updated trusted tools" || true

.PHONY: lint update_trusted help
