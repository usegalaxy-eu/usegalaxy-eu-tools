lint: lint-yaml lint-sections

lint-yaml:
	yamllint .

lint-sections:
	python scripts/validate-section.py

.PHONY: lint lint-yaml lint-sections
