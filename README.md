# ATOMS Sensemaking

**atoms-sensemaking** is a microservice that provides analytics for ATOMS data.

- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Usage](#usage)
- [Docs](#references)

## Prerequisites

### Required

- [Docker](https://docs.docker.com/desktop/setup/install/mac-install/)
- [pyenv](https://formulae.brew.sh/formula/pyenv)

### Other

- [brew](https://brew.sh/)
- [Git](https://formulae.brew.sh/formula/git)
- [Git LFS](https://formulae.brew.sh/formula/git-lfs)
- [mkdocs](https://formulae.brew.sh/formula/mkdocs)
- [Postman](https://www.postman.com/downloads/)

## Setup

### Certificates

Decrypt certificates:

```bash
  bin/transcrypt -c aes-256-cbc -p <ask-for-password>
```

### Environment Variables

Generate `.env` with the local template:

```bash
  cp .env.template .env
```

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

```
which python3  # should point to .venv/bin/python3
python -V      # should match .python-version
```

Install dependencies:

```bash
  make install
```

## Usage

- Run services: `make up`
- Stop services: `make down`

## Docs

See [Docs](docs/) for more information.

- [Development Guide](docs/dev-guide/dev.md)
- [Environment Variables](docs/dev-guide/env-vars.md)
- [Packaging & Versioning](docs/dev-guide/packaging.md)
- [Example Settings for AIDE](docs/dev-guide/aide-env.md)

### mkdocs

- Serve [locally](http://localhost:4000): `mkdocs serve`
- Build in [site](site/) directory: `mkdocs build`
