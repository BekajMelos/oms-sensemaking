SHELL := /bin/bash

.PHONY: help test build clean distclean

## NOTE: Add this to your .bashrc to enable make target tab completion
##    complete -W "\`grep -oE '^[a-zA-Z0-9_.-]+:([^=]|$)' ?akefile | sed 's/[^a-zA-Z0-9_.-]*$//'\`" make
## Reference: https://stackoverflow.com/a/38415982

help: ## Display this help message
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

test: ## Run integration tests
	python -m pytest $(PYTEST_FLAGS)

build: ## Build the project artifacts (i.e. wheel and tarball)
	python -m build

clean: ## Purge build artifacts
	@rm -rf dist/*.whl dist/*.tar.gz dist/*.zip

distclean: clean  ## Purge all generated 
	@rm -rf src/oms_sensemaking*.egg-info
