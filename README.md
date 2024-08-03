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

### Setting Up A Development Environment:

#### Step 1: Create a Virtual Environment

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

#### Step 2: Install Project Dependencies

1. Upgrade *pip* and *wheel*

    ```sh
    pip install --upgrade pip wheel
    ```

2. Install Development and Runtime Dependencies

    ```sh
    pip install -r requirements.txt
    ```

#### Step 3: Configure Local Environment Variables

The module expects certain environment variables to be set. This can be
accomplished by creating a .env file and setting the environment variables
there. This file will be detected and read at runtime.

```
cp .env.template .env
```

#### Step 4: Configure git authentication

Create a `.netrc` file in your home directory:

```
# ~/.netrc

machine tex.gerbil-cloud.ts.net
login your-login-here
password "your password here"
```

#### Environment Settings
```
# Geospatial Sensemaking Settings
DEBUG=True                              # Option to see DEBUG log level
VALID_OBSERVED_THRESHOLD_SECONDS=900    # Threshold for amount of between Track Point Observations
CACHE_ENTRY_EXPIRE_SEC=5                # How long to wait for new points before creating a new Track
GEOHASH_LOW=5                           # Low geohash
GEOHASH_HIGH=7                          # High geohash
POLL_PERIOD_SECONDS=10                  # How often to poll for new incoming Attributes

# Loiter Settings
DETECT_LOITERS=True                     # Toggle on/off Loiter Detection
LOITER_MIN_TIME=900                     # Minimum amount of time for a valid Loiter Event

# Cotravel Settings
DETECT_COTRAVELS=True                   # Toggle on/off Cotravel Detection
MIN_COTRAVEL_DURATION_SECONDS=1200      # Minimum between Objects in a Track for a Cotravel Event
MIN_LAG_LEAD_DURATION_SECONDS=1200      # Minimum amount between Objects in a Track for a Lag/Lead Event
MAX_LAG_LEAD_DURATION_SECONDS=2700      # Maximum between Objects in a Track for a Lag/Lead Event

# Similar Track Settings
SIMILAR_TRACKS=False                    # Toggle on/off Similar Track Calculations
N_TRACKS=5                              # Number of similar tracks to return
WITHIN_METERS=3000.0                    # Used to define the search space for potential similar tracks
```

### Code Quality

The *oms-sensemaking* project is configured to use [ruff] for code linting and
formatting and [mypy] for type checking (see the relevant tables in pyproject.toml).

*ruff* can be run directly on the command line and integrated into your editor
and/or SCM. There is also a [Makefile] that wraps the code quality and build
commands into a convienient interface. Run `make help` for more information.


#### Code Linting

To run ruff's linter from the command line:

```
ruff check
```

Alternatively, you can run `make lint` which will run ruff's linter and mypy.

> ***TIP***: You can also use `ruff check --fix` or `make fix` to
> automatically fix a subset of linting issues that ruff deems "safe".


#### Code Formatting

Using `ruff check` and `ruff check --fix` may be sufficient to keep the
codebase reasonably consistent. If needed, ruff also has a code formatter that
aims to be compatible with [black].

> Both *black* and *ruff format* are opinionated tools, and might be overkill.

To run the formatter from the command line:

```
ruff format
```

or

```
make format
```

#### Integrating Code Quality Tools

##### pre-commit

To integrate ruff with the project's SCM via [pre-commit] and Git's pre-commit hooks:

```
pre-commit install
```

> This will use the configuration in [.pre-commit-config.yaml]

##### Visual Studio Code

To integrate with Visual Studio Code, use the [Ruff extension for Visual Studio Code]
and/or the [MyPy extension for Visual Studio Code]

##### PyCharm

To integrate with PyCharm, use the [PyCharm Ruff plugin].

## Running the Application
```
python -m oms_sensemaking geo data/simple_cotravel_example.csv
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

> ***NOTE***: The project version is determined dynamically based on the
> project's git repository using [setuptools-scm].


[pyenv]: https://github.com/yyuu/pyenv
[Python]: https://www.python.org
[.pre-commit-config.yaml]: ./.pre-commit-config.yaml
[.python-version]: ./.python-version
[setuptools-scm]: https://setuptools-scm.readthedocs.io
[ruff]: https://docs.astral.sh/ruff
[Ruff extension for Visual Studio Code]: https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff
[MyPy extension for Visual Studio Code]: https://marketplace.visualstudio.com/items?itemName=ms-python.mypy-type-checker
[PyCharm Ruff plugin]: https://plugins.jetbrains.com/plugin/20574-ruff
[black]: https://github.com/psf/black
[mypy]: https://mypy-lang.org
[Makefile]: ./Makefile
