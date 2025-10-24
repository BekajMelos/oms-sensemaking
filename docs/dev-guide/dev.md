# Development Environment

A quick development guide for `atoms-sensemaking`.

- [Setup](#setup)
- [Common Workflows](#common-workflows)
  - [Services](#services)
  - [Manage Containers](#manage-containers)
  - [Code Quality](#code-quality)
  - [Code Testing](#code-testing)
  - [API Testing](#api-testing-postman)
- [Utilities](#utilities)

## Setup

In [README](../../README.md), follow all Prerequisites and Setup steps.

Ask a teammate for supplemental references to:

- Setup additional variables in `.env`.
- Configure Access Tokens in `~/.netrc`.
- Configure pip to use a private PyPI in `.venv/pip.conf`.

## Common Workflows

### Services

- Start services: `make up`
- Stop services: `make down`

### Manage containers

- Remove volumes: `make nuke`
- Remove volumes, rebuild containers with updated dependencies: `make refresh`

### Code Quality

- Format code: `make format`
- Lint code: `make fix`
- Lint check: `make lint`

### Code Testing

- Run unit and integration tests: `make test`

### API Testing (Postman)

In [Postman](https://www.postman.com/downloads/), "Import" the [postman](../../postman) directory. 
Use the `Sensemaking OMS Localhost` environment while running the `Sensemaking Smoke Tests`.

## Utilities

See the [scripts](../../scripts) directory for various developer utilites.

- [Load Testing & Queue Performance Metrics](load-test.md)
- [pgAdmin](http://localhost:5050) for Postgres: `make pgadmin`