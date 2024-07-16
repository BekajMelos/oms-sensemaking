# OMS Sensemaking Module

Python module used to perform analytics on OMS data.


## Development Environment

*oms-sensemaker* uses [Python] 3.10. The specific instructions for installing
Python varies across platforms. You will want to verify that the version you are
using matches the version defined in [.python-version].

> ***TIP***: When possible, use a tool like [pyenv] to help manage the version
> of Python that you are using. This project includes a [.python-version] file
> which pyenv will leverage to ensure you have the correct version of Python
> installed.

To setup your local development environment:

### Step 1: Create a Virtual Environment

Use the built-in venv module to create a virtual environment for the new
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

### Step 2: Install Project Dependencies

1. Upgrade *pip* and *wheel*

    ```sh
    pip install --upgrade pip wheel
    ```

2. Install Development and Runtime Dependencies

    ```sh
    pip install -r requirements.txt
    ```

### Step 3: Configure Local Environment

The module expects certain environment variables to be set. This can be
accomplished by creating a .env file and setting the environment variables
there. This file will be detected and read at runtime.

```
cp .env.template .env
```

### Step 4: Code Linting/Formatting

The *oms-sensemaking* project is configured to use [ruff] for code linting and
formatting (see the relevant tables in pyproject.toml).

*ruff* can be run directly on the command line and integrated into your editor
and/or SCM.

To run the linter from the command line:

```
ruff check
```

To run the formatter from the command line:

```
ruff format
```

To integrate with the project's SCM via [pre-commit] and Git's pre-commit hooks:

```
pre-commit install
```

> This will use the configuration in [.pre-commit-config.yaml]

To integrate with Visual Studio Code:

See [Ruff extension for Visual Studio Code]


## Running Unit Tests

```
pytest
```


## Building

To package the project for distribution:

```
make build
```

This command will build a Python wheel as well as an archive of the source code
and store the results in the *dist* directory.

> ***NOTE***: The project version is determined dynamically based on the
> project's git repository using [setuptools-scm].


[pyenv]: https://github.com/yyuu/pyenv
[Python]: https://www.python.org
[.pre-commit-config.yaml]: ./.pre-commit-config.yaml
[.python-version]: ./.python-version
[setuptools-scm]: https://setuptools-scm.readthedocs.io
[ruff]: https://docs.astral.sh/ruff/
[Ruff extension for Visual Studio Code]: https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff
