# OMS Sensemaking

**oms-sensemaking** is a microservice that provides analytics for OMS data.

- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Usage](#usage)
- [References](#references)

## Prerequisites

- [Docker](https://docs.docker.com/desktop/setup/install/mac-install/)
- [pyenv](https://formulae.brew.sh/formula/pyenv)
- [Git](https://formulae.brew.sh/formula/git)
- [Git LFS](https://formulae.brew.sh/formula/git-lfs)

## Setup

### Certificates

Decrypt certificates with transcrypt:

```bash
bin/transcrypt -c aes-256-cbc -p <password>
```

- Ask a teammate for the password.

### Environment Variables

Generate `.env` with the local template:

```bash
cp .env.template .env
```

- Ask a teammate for guidance on setting `PIP_INDEX` and `DOCKER_REGISTRY`.

### Python

Install according to `.python-version`:

```bash
pyenv install
```

Create and activate the virtual environment:

```bash
pyenv exec python -m venv .venv
source .venv/bin/activate
```

Verify installation:

```text
which python3       # should point to .venv/bin/python3
python -V           # should match .python-version
```

Install dependencies:

```bash
make install
```

## Usage

- Run services: `make up`
- Stop services: `make down`
- Remove volumes: `make nuke`

## References

Supplemental references are available. Ask a teammate for guidance.

- [Docs](docs)
  - [Development Guide](docs/dev-guide)
  - [Track Weaving](docs/track-weaving)
  - [Project Index](docs/index.md)
