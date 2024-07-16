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

```
cp .env.template .env
```


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

> ***NOTE***: The project version is determined dynamically based on the project's git repository using [setuptools-scm].


[pyenv]: https://github.com/yyuu/pyenv
[Python]: https://www.python.org
[.python-version]: ./.python-version
[setuptools-scm]: https://setuptools-scm.readthedocs.io
