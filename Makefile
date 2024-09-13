SHELL := /bin/bash

.PHONY: build build-docker clean distclean down fix format help lint lint-stats nuke pgadmin psql test up

## NOTE: Add this to your .bashrc to enable make target tab completion
##    complete -W "\`grep -oE '^[a-zA-Z0-9_.-]+:([^=]|$)' ?akefile | sed 's/[^a-zA-Z0-9_.-]*$//'\`" make
## Reference: https://stackoverflow.com/a/38415982

help: ## Display this help message
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

test: ## Run integration tests
	python -m pytest $(PYTEST_FLAGS)

build: ## Build the project artifacts (i.e. wheel and tarball)
	python -m build

lint:  ## Run linter
	ruff check
	mypy src

lint-stats:
	ruff check --statistics

local: ## Start oms-sensemaking locally
	uvicorn oms_sensemaking.service:app --port 5000 --reload --log-level debug

local-env: ## start oms-sensemaking with supporting oms env containers
	docker compose --profile local up -d

fix:  ## Run linter and apply fixes
	ruff check --fix

format:  ## Run the formatter
	ruff format

build-docker:  ## Build docker image
	docker build --build-arg APP_VERSION=$(shell source .venv/bin/activate && python -m setuptools_scm) --no-cache -t oms_sensemaking:latest --secret id=mynetrc,src=$${HOME}/.netrc .

version:  ## Display the project version
	@echo $(shell source .venv/bin/activate && python -m setuptools_scm)

up: ## Start oms-sensemaking in docker. Force build with: DOCKER_FLAGS=--build make up
	docker compose up -d ${DOCKER_FLAGS}

down: ## Stop oms-sensemaking docker environment
	docker compose --profile dev --profile local down

psql: ## psql into main db
	docker compose exec postgis psql -h postgis

pgadmin: ## start pgadmin (kill it with: docker-compose --profile dev down)
	docker compose --profile dev up pgadmin -d

clean: ## Purge build artifacts
	@rm -rf dist/*.whl dist/*.tar.gz dist/*.zip

distclean: clean  ## Purge all generated content
	@rm -rf src/oms_sensemaking*.egg-info

nuke: down
	@docker volume rm -f oms-sensemaking_localstack
	@docker volume rm -f oms-sensemaking_pgadmin
	@docker volume rm -f oms-sensemaking_postgis
	@docker volume rm -f oms-sensemaking_zookeeper_data
	@docker volume rm -f oms-sensemaking_zookeeper_datalog
