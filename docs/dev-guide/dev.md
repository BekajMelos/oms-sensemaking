# Development Environment

*oms-sensemaker* uses [Python] 3.12. The specific instructions for installing
Python varies across platforms. You will want to verify that the version you are
using matches the version defined in `.python-version`.

> ***TIP***: When possible, use a tool like [pyenv] to help manage the version
> of Python that you are using. This project includes a `.python-version` file
> which pyenv will leverage to ensure you have the correct version of Python
> installed.

## Setting Up A Development Environment:

### Step 1: Install Docker

See the [Install Docker Engine] section of the Docker Manual for platform
specific installation instructions.

### Step 1: Create a Virtual Environment

Use the built-in [venv] module to create a virtual environment for the new
project. This virtual environment will be used to isolate the projects
dependencies.

The following example uses a hidden local directory to store the virtual
environment. This directory will be excluded from git based on the rules in the
*.gitignore* file.

> *TIP*: You can set a prompt for the virtual environment using the `--prompt`
> option. If your shell supports it, this will add a prefix to the command
> prompt with the project name (or whatever you set it to).

```sh
python -m venv --prompt sensemaking .venv  # create virtual environment
source .venv/bin/activate                  # activate virtual environment
```

### Step 2: Configure Private PyPI

Ask a teammate for guidance.

### Step 3: Install Project Dependencies

- Upgrade *pip* and *wheel*
- Install *Development*, *Run Time*, and *Built Time* Dependencies
- Integrate ruff with the project's SCM via [pre-commit] and Git's pre-commit hooks (configured in `.pre-commit-config.yaml`)

These are handled by running the following make command:

```
make install
```


### Step 4: Configure Local Environment Variables

The module expects certain environment variables to be set. This can be
accomplished by creating a `.env` file and setting the environment variables
there. This file will be detected and read at runtime.

```
cp .env.template .env
```

> For a full list of environment variables that can be configured this way,
> see [Environment Variables].

At a minimum, you will need to have the following variables set, everything else
will rely on the default values set in the applicaton's configuraton:

| Variable Name       | Example                                           | Description                                           |
|:--------------------|:--------------------------------------------------|:------------------------------------------------------|
| `POSTGRES_PASSWORD` | `xxxxxxx`                                         | The password for the PostgreSQL admmin user           |
| `OMSB_VERSION`      | `Grimlock-INC-21`                                 | The version of oms-bridge                             |
| `OMSB_URL`          | `https://localhost:8020/graphql`                  | URL for OMSB                                          |
| `CERT_PATH`         | `./pki/test10.pem`                                | Path to User PEM                                      |
| `KEY_PATH`          | `./pki/test10.key`                                | Path to User Key                                      |
| `DOCKER_REGISTRY`   | `hostname:5000`                                   | Socket address of the remote docker registry          |
| `PIP_INDEX`         | `https://host:3000/api/packages/oms/pypi/simple`  | URL for the private pip index                         |


### Step 5: Decrypt Certs

Run `bin/transcrypt` with the following options to decrypt secrets:

- Encryption: `aes-256-cbc`
- Generate Password: `no`
- Password: *ask a team member for the password*


### Step 6: Verify Your Local Configuration
Run `make up` to start the containers. To verify that your local configuration is working, you can run the project's unit tests:

```
make test
```
## Code Quality

The *oms-sensemaking* project is configured to use [ruff] for code linting and
formatting and [mypy] for type checking (see the relevant tables in pyproject.toml).

*ruff* can be run directly on the command line and integrated into your editor
and/or SCM. There is also a [Makefile] that wraps the code quality and build
commands into a convienient interface. Run `make help` for more information.


### Code Linting

To run ruff's linter from the command line:

```
ruff check
```

Alternatively, you can run `make lint` which will run ruff's linter and mypy.

> ***TIP***: You can also use `ruff check --fix` or `make fix` to
> automatically fix a subset of linting issues that ruff deems "safe".


### Code Formatting

> ***WARNING***: Both *black* and *ruff format* are opinionated tools, and might
> be overkill.

Using `ruff check` and `ruff check --fix` may be sufficient to keep the
codebase reasonably consistent. If needed, ruff also has a code formatter that
aims to be compatible with [black].

To run the formatter from the command line:

```
ruff format
```

or

```
make format
```

### Integrating Code Quality Tools

#### Visual Studio Code

To integrate with Visual Studio Code, use the [Ruff extension for Visual Studio Code]
and/or the [MyPy extension for Visual Studio Code]

#### PyCharm

To integrate with PyCharm, use the [PyCharm Ruff plugin].


#### Relevant links

Ask a teammate for guidance.
