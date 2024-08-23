# OMS Sensemaking

Microservice that performs analytics on OMS data.


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

#### Step 2: Configure git authentication

*oms-sensemaking* includes a dependency on the [oms-sdk] that is defined using a
[PEP 508] compatible URL to the oms-sdk project's Git repository, which will
require authentication. You can configure your local system to authenticate
automatically using a local [.netrc] file.

Create a `.netrc` file in your home directory:

```
# ~/.netrc

machine tex.gerbil-cloud.ts.net
login your-login-here
password "your password"
```

#### Step 3: Install Project Dependencies

1. Upgrade *pip* and *wheel*

    ```sh
    pip install --upgrade pip wheel
    ```

2. Install *Development*, *Run Time*, and *Built Time* Dependencies

    ```sh
    pip install -e ".[dev,test,build]"
    ```

> ***NOTE***: *oms_sensemaking* has at least two "extra" sets of dependencies defined: "dev" and "test". see the `project.optional-dependencies` declaration in [pytproject.toml].

#### Step 4: Configure Local Environment Variables

The module expects certain environment variables to be set. This can be
accomplished by creating a .env file and setting the environment variables
there. This file will be detected and read at runtime.

```
cp .env.template .env
```

##### Environment Settings

Create a `.netrc` file in your home directory:

```
# ~/.netrc

machine tex.gerbil-cloud.ts.net
login your-login-here
password "your password here"
```

#### Environment Settings

| Variable  | Example  | Description |
|:------------- |:---------------:| -------------:|
| `LOG_LEVEL`  | DEBUG | Option to set log level |
| `POSTGRES_USER` | postgres | The default PostgreSQL/PostGIS admin user |
| `POSTGRES_PASSWORD` || The password for the default PostgreSQL/PostGIS admmin user |
| `PGUSER` | appuser | [psql] The *regular* PostgreSQL/PostGIS user |
| `PGPASSWORD` | password | [psql] The password for the *regular* PostgreSQL/PostGIS |
| `PGDATABASE` | oms_sensemaking | [psql] The database to connect to |
| `VALID_OBSERVED_THRESHOLD_SECONDS`  | 900 | Threshold for amount of between Track Point Observations |
| `CACHE_ENTRY_EXPIRE_SEC`  | 30 | How long to wait for new points before creating a new Track |
| `GEOHASH_LOW`  | 5 | Low geohash |
| `GEOHASH_HIGH`  | 7 | High geohash |
| `POLL_PERIOD_SECONDS`  | 10 | How often to poll for new incoming Attributes |
| `OPERATED_BY_IRI`  | http://schema.dia.mil/DefenseIntelligenceCoreOntology/operatedBy | IRI for Operated By |
| `DETECT_LOITERS`  | True | Toggle on/off Loiter Detection |
| `LOITER_MIN_TIME`  | 900 | Minimum amount of time for a valid Loiter Event |
| `DETECT_COTRAVELS`  | True | Toggle on/off Cotravel Detection |
| `MIN_COTRAVEL_DURATION_SECONDS`  | 1200 | Minimum between Objects in a Track for a Cotravel Event |
| `MIN_LAG_LEAD_DURATION_SECONDS`  | 1200 | Minimum amount between Objects in a Track for a Lag/Lead Event |
| `MAX_LAG_LEAD_DURATION_SECONDS`  | 2700 | Maximum between Objects in a Track for a Lag/Lead Event |
| `SIMILAR_TRACKS`  | True | Toggle on/off Similar Track Calculations |
| `N_TRACKS`  | 5 | Number of similar tracks to return |
| `WITHIN_METERS`  | 3000.0 | Used to define the search space for potential similar tracks |
| `QUEUE_URL`  | http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/geoSensemakerTrigger | SQS Queue URL |
| `AWS_ENDPOINT_URL`  | http://localhost:4566 | SQS Endpoint |
| `AWS_ACCESS_KEY_ID`  | FAKE | AWS Access Key |
| `AWS_SECRET_ACCESS_KEY`  | FAKE | AWS Secret Key |
| `AWS_REGION_NAME`  | us-east-1 | AWS Region |
| `AWS_USE_SSL`  | False | Boolean to use SSL for SQS Connection |
| `AWS_VERIFY`  | False | Boolean to use SSL verifiation for SQS Connection |
| `OMSB_URL`  | https://localhost:8443/graphql | URL for OMSB |
| `USER_DN`  | cn=test10,ou=jade,ou=meme,o=bia,st=maryland,c=us | User DN |
| `CERT_PATH`  | ./pki/test10.pem | Path to User PEM |
| `KEY_PATH`  | ./pki/test10.key | Path to User Key |


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
# Run and listen for events from sqs
python -m oms_sensemaking geo
# Run and read events from local file
python -m oms_sensemaking geo --filename data/N11QN_202212011800.csv
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


[Makefile]: ./Makefile
[pyproject.toml]: ./pyproject.toml
[.pre-commit-config.yaml]: ./.pre-commit-config.yaml
[.python-version]: ./.python-version
[pyenv]: https://github.com/yyuu/pyenv
[Python]: https://www.python.org
[setuptools-scm]: https://setuptools-scm.readthedocs.io
[ruff]: https://docs.astral.sh/ruff
[Ruff extension for Visual Studio Code]: https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff
[MyPy extension for Visual Studio Code]: https://marketplace.visualstudio.com/items?itemName=ms-python.mypy-type-checker
[PyCharm Ruff plugin]: https://plugins.jetbrains.com/plugin/20574-ruff
[black]: https://github.com/psf/black
[mypy]: https://mypy-lang.org
[venv]: https://docs.python.org/3/library/venv.html
[.netrc]: https://www.gnu.org/software/inetutils/manual/html_node/The-_002enetrc-file.html
[oms-sdk]: https://tex.gerbil-cloud.ts.net:3000/data-team/omsb-2-common-utils-python
[PEP 508]: https://peps.python.org/pep-0508/

