# Atoms Dev Local Environment

This document helps developers spin up the atoms dev local environment
for local development.

## Setup

1. Clone the `atoms-local-dev` repository and follow the steps in that repo to get started.
    - In `local.dev.env` change `DOCKER_REGISTRY` environment variable to point to our local registry
    - Depending on if testing against `Grimlock` or `Starscream` versions, change `DOCKER_FILE` to point to the right
    compose file in `local.dev.env`
    - In `local.dev.env` change the `COMPOSE_PROFILES` environment variable to include/exclude certain containers. Do
    not include `sensemaking`.
2. Clone the `oms-sensemaking` repository and follow steps in that repo to get started.
    - In `.env` change `POSTGRES_PASSWORD` to match the password in the `atoms-local-dev` repo.
    - In `.env` change `OMSB_VERSION` to the version of `Grimlock` or `Starscream` building against.
    - Run `make install refresh`

To bring down containers:

- In oms-sensmaking `make down` or `make nuke`.
