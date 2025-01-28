# OMS Sensemaking

Microservice that provides analytics for OMS data.

## Before You Begin

1. Install [Git] and [Git LFS]

   If you are using a Mac, consider installing Git LFS with Homebrew: `brew
   install git-lfs`

2. Install Docker

   See the [Install Docker Engine] section of the Docker Manual for platform
   specific installation instructions.

3. Install Python

   It is recommended that you use [pyenv] to install the version of Python
   defined by the projects `.python-version` file.

   ```
   $ pyenv install
   ```

## Quickstart

> ***TIP***: The [Setting up an OMS Sensemaking Development Environment]
> section of the *OMS Development Guide* covers development environment setup
> in more detail. This file can also be found locally: `docs/dev-guide/dev.md`.

1. Ensure you are using the correct version of Python

   ```
   $ pyenv install
   ```

2. Create a virtual environment using Python's built-in venv module

   ```
   $ pyenv exec python -m venv --prompt sensemaking .venv  # create the virtual environment
   $ source .venv/bin/activate                  # activate the virtual environment
   $ pip install --upgrade pip wheel            # update the core packaging tools
   ```

> ***TIP***: After activating the virtual environment, run `which python3` to verify it's looking
> at `<path_to_oms-sensemaking>/.venv/bin/python3` and run `python -V` to verify the version matches what's
> in `.python-version`

3. Configure pip to use Gitea's private PyPI

   Create a `~/.netrc` file:

   ```
   # ~/.netrc
   machine tex.gerbil-cloud.ts.net
   login your-login-here
   password "your password"
   ```

   Create a project-level configuration in `.venv/pip.conf`:

   ```
   # .venv/pip.conf --- local project pip configuration.
   [global]
   index-url = https://tex.gerbil-cloud.ts.net:3000/api/packages/oms/pypi/simple
   extra-index-url = https://pypi.org/simple
   ```

4. Install Project Dependencies

   ```
   $ pip install -e ".[dev,docs,test,build]"
   ```

5. Decrypt Certs

   Run `bin/transcrypt` with the following options to decrypt secrets:

    - Encryption: `aes-256-cbc`
    - Generate Password: `no`
    - Password: *ask a team member for the password*

The project documentation includes a development guide that covers development
environment configuration, application configuration, and packaging as well as a
dynamically generated API reference and OMS Sensemaking quickstart guide. Once
you have a development environment installed, you can host a local copy of the
project documentation with `mkdocs serve`, which will host the project at
http://localhost:4000 or build a static copy with `mkdocs build` (the resulting
static site will be located in the `site` directory).


[Install Docker Engine]: https://docs.docker.com/engine/install/

[pyenv]: https://github.com/pyenv/pyenv

[Setting up an OMS Sensemaking Development Environment]: https://tex.gerbil-cloud.ts.net:3000/oms/oms-sensemaking/src/branch/main/docs/dev-guide/dev.md

[mkdocs]: https://www.mkdocs.org/

[mkdocstring]: https://mkdocstrings.github.io/

[Git]: https://git-scm.com/

[Git LFS]: https://git-lfs.com/
