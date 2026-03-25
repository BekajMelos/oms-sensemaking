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

### Environment Variables

> See [Environment Settings](env-vars.md) for a full list of environment variables that can be configured.

At a minimum, you will need to set the below variables. Others may rely on the default values set in the
applicaton's configuraton.

| Variable Name | Example                                          | Description |
|:--------------------|:-------------------------------------------------|:------------------------------------------------------|
| `OMSB_VERSION` | `3.1.6`                                          | The version of Atoms Core |
| `OMSB_URL` | `https://localhost:8020/graphql`                 | URL for OMSB |
| `CERT_PATH` | `./etc/pki/test10.pem`                           | Path to User PEM |
| `KEY_PATH` | `./etc/pki/test10.key`                           | Path to User Key |
| `ATOMS_CACERT_PATH` | `./etc/pki/trusted.crt`                          | Path to CA File used for your local dev containers |
| `DOCKER_REGISTRY` | `hostname:5000`                                  | Socket address of the remote docker registry |
| `PIP_INDEX` | `https://host:3000/api/packages/oms/pypi/simple` | URL for the private pip index |
| `ATOMS_LOCAL_DEV` | `../atoms-local-dev`                             | Path to the atoms-local-dev repo |

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
Use the `Sensemaking ATOMS Localhost` environment while running the `Sensemaking Smoke Tests`.

## Utilities

See the [scripts](../../scripts) directory for various developer utilites.

- [Load Testing & Queue Performance Metrics](load-test.md)
- [pgAdmin](http://localhost:5050) for Postgres: `make pgadmin`
