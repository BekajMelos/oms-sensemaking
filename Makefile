SHELL := /bin/bash

include .env
export

.PHONY: build build-docker build-docs clean distclean down fix format help lint lint-stats no-oms nuke pgadmin psql shell test up metrics-up load-out-of-garrison

## NOTE: Add this to your .bashrc to enable make target tab completion
##    complete -W "\`grep -oE '^[a-zA-Z0-9_.-]+:([^=]|$)' ?akefile | sed 's/[^a-zA-Z0-9_.-]*$//'\`" make
## Reference: https://stackoverflow.com/a/38415982

limit ?= 100
loop ?= 1
loop_wait ?= 0

help: ## Display this help message
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Run upgrades and installations to prepare the repository
	pip install --upgrade pip wheel
	pip install -e ".[dev,docs,test,build]"
	pre-commit install

test: ## Run all tests
	python -m pytest $(PYTEST_FLAGS) --cov-fail-under=80

unit-test: ## Run unit tests
	python -m pytest tests $(PYTEST_FLAGS) --cov-fail-under=79.5

int-test: ## Run integration tests
	python -m pytest tests_int $(PYTEST_FLAGS)

build: ## Build the project artifacts (i.e. wheel and tarball)
	python -m build

lint:  ## Run linter
	ruff check
	mypy src

lint-stats:
	ruff check --statistics

local: ## Start atoms-sensemaking locally
	uvicorn oms_sensemaking.service:app --port 5000 --reload --log-level debug

no-atoms: ## start atoms-sensemaking without supporting atoms env containers
	docker compose up -d

fix:  ## Run linter and apply fixes
	ruff check --fix

format:  ## Run the formatter
	ruff format

bundle:
	scripts/bundle.sh

build-docker:  ## Build docker image
	docker build \
          --build-arg APP_VERSION=$(shell source .venv/bin/activate && python -m setuptools_scm) \
          --build-arg BUILD_DATE=$(shell date +%Y%m%d%H%M) \
          --build-arg VCS_REF=$(shell git rev-parse --short HEAD) \
		  --build-arg PIP_INDEX_URL=${PIP_INDEX} \
		  --build-arg PIP_EXTRA_INDEX_URL=${PIP_EXTRA_INDEX} \
          --no-cache \
          -t oms_sensemaking:latest \
          --secret id=mynetrc,src=$${HOME}/.netrc \
          --platform linux/amd64,linux/arm64 \
          .

build-docs:  ## Build project documentation static site.
	mkdocs build

version:  ## Display the project version
	@echo $(shell source .venv/bin/activate && python -m setuptools_scm)

list-versions: ## Display the tagged versions
	@git tag -n

up: ## Start atoms-sensemaking in docker. Force build with: DOCKER_FLAGS=--build make up
	docker compose up -d ${DOCKER_FLAGS}

stop: ## Stop atoms-sensemaking docker environment
	docker compose stop

down: ## Stop atoms-sensemaking docker environment and remove containers
	docker compose down

shell: ## Open a shell inside the atoms_sensemaking container
	@docker compose exec atoms_sensemaking /bin/bash

psql: ## psql into main db
	docker compose exec postgis psql -h postgis

pgadmin: ## start pgadmin (kill it with: docker-compose --profile dev down)
	@docker compose up pgadmin -d

tools: ## start dev tools (kill it with: docker-compose --profile dev down)
	@COMPOSE_PROFILES="$${COMPOSE_PROFILES},dev,tools"; \
	docker compose --profile dev --profile tools up -d

clean: ## Purge build artifacts
	@rm -rf dist/*.whl dist/*.tar.gz dist/*.zip

distclean: clean  ## Purge all generated content
	@rm -rf src/oms_sensemaking*.egg-info

nuke:
	@COMPOSE_PROFILES="$${COMPOSE_PROFILES},dev,tools"; \
	docker compose down -v

refresh: nuke  # Purge all generated content and restart
	@COMPOSE_PROFILES="$${COMPOSE_PROFILES},dev,tools"; \
	docker compose --profile local up --build -d

load-out-of-garrison:
	python -m scripts.load_test.main --limit $(limit) --loop $(loop) --loop-wait $(loop_wait)