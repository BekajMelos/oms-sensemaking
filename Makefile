# Copyright Black Cape, Inc 2024.
# Use of this software is governed by the LICENSE.md file.
SHELL := /bin/bash

PYTEST_FLAGS=-s --show-capture=no --cov-config=tests/.coveragerc --cov=oms-sensemaking --cov-report term --cov-report html

.PHONY: help test

## NOTE: Add this to your .bashrc to enable make target tab completion
##    complete -W "\`grep -oE '^[a-zA-Z0-9_.-]+:([^=]|$)' ?akefile | sed 's/[^a-zA-Z0-9_.-]*$//'\`" make
## Reference: https://stackoverflow.com/a/38415982

help: ## Display this help message
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

test: ## Run integration tests
#	python -B -m pytest -ra ${PYTEST_FLAGS}
	pytest

build: ## Build the project artifacts (i.e. wheel and tarball)
	python -m build

clean: ## Purge build artifacts
	@rm -rf dist/*.whl dist/*.tar.gz dist/*.zip

