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

> ***NOTE***: The *Docker Compose* column indicates if setting the variable in
> `.env` will carry over to one or more of the containers defined in
> `docker-compose.yml`. The variables that do not carry over either rely on a
> sensible default value or are configured directly in `docker-compose.yml`.


##### Service Variables

| Variable Name   | Example | Description                                                    | Docker Compose |
|:----------------|:--------|:---------------------------------------------------------------|:--------------:|
| `APP_LOG_LEVEL` | `DEBUG` | Option to set log level                                        | Yes            |
| `RELOAD_APP`    | `1`     | Option to watch for changes and reload service (i.e. dev mode) | Yes            |


##### Database Settings

> ***NOTE***: There are two database users that need to be configured (i.e.
> admin user and a regular user). There are also three different tools being
> configured by docker: the *oms_sensemaking* service, the psql command line
> tool, and [pgAdmin].


| Variable Name                 | Example                           | Description                                           | Docker Compose |
|:------------------------------|:----------------------------------|:------------------------------------------------------|:--------------:|
| `DB_HOST`                     | `postgis`                         | The database hostname                                 | No             |
| `DB_USER`                     | `appuser`                         | The regular (i.e. non-admin) username.                | Yes            |
| `DB_PASSWORD`                 | `xxxxxx`                          | The password for the regular db user.                 | Yes            |
| `POSTGRES_USER`               | `postgres`                        | The PostgreSQL/PostGIS admin user                     | Yes            |
| `POSTGRES_PASSWORD`           | `xxxxxxx`                         | The password for the PostgreSQL admmin user           | Yes            |
| `PGUSER`                      | `appuser`                         | [psql] The *regular* PostgreSQL user                  | Yes            |
| `PGPASSWORD`                  | `xxxxxx`                          | [psql] The password for the *regular* PostgreSQL user | Yes            |
| `PGDATABASE`                  | `oms_sensemaking`                 | [psql] The database to connect to                     | Yes            |
| `PGADMIN_DEFAULT_EMAIL`       | `dev@blackcape.io`                | [pgAdmin] The login for the default pgAdmin user.     | Yes            |
| `PGADMIN_DEFAULT_PASSWORD`    | `xxxxxx`                          | [pgAdmin]The password for the default pgAdmin user.   | Yes            |
| `PGADMIN_CONFIG_LOGIN_BANNER` | `'<h4>Development Database</h4>'` | [pgAdmin]A login banner for pgAdmin                   | Yes            |


##### AWS Settings

| Variable Name           | Example                                             | Description                           | Docker Compose |
|:------------------------|:----------------------------------------------------|:--------------------------------------|:--------------:|
| `AWS_ENDPOINT_URL`      | `http://localhost:4566` or `http://localstack:4566` | AWS Endpoint                          | No             |
| `AWS_ACCESS_KEY_ID`     | `FAKE`                                              | AWS Access Key                        | No             |
| `AWS_SECRET_ACCESS_KEY` | `FAKE`                                              | AWS Secret Key                        | No             |
| `AWS_REGION_NAME`       | `us-east-1`                                         | AWS Region                            | No             |
| `AWS_USE_SSL`           | `False`                                             | Boolean to use SSL for SQS Connection | No             |
| `AWS_VERIFY`            | `False`                                             | Boolean to use SSL verifiation        | No             |


##### OMSB Settings

| Variable Name  | Example                                            | Description               | Docker Compose |
|:---------------|:---------------------------------------------------|:--------------------------|:--------------:|
| `OMSB_VERSION` | `Grimlock-INC-4`                                   | The version of oms-bridge | Yes            |
| `OMSB_URL`     | `https://localhost:8443/graphql`                   | URL for OMSB              | No             |
| `USER_DN`      | `cn=test10,ou=jade,ou=meme,o=bia,st=maryland,c=us` | User DN                   | No             |
| `CERT_PATH`    | `./pki/test10.pem`                                 | Path to User PEM          | No             |
| `KEY_PATH`     | `./pki/test10.key`                                 | Path to User Key          | No             |




##### Sensemaker Settings

| Variable Name                      | Example                                                            | Description                                                    | Docker Compose |
|:-----------------------------------|:-------------------------------------------------------------------|:---------------------------------------------------------------|:--------------:|
| `SRID`                             | `4326`                                                             | Spatial Reference Identifier for storing Points       | No             |
| `VALID_OBSERVED_THRESHOLD_SECONDS` | `900`                                                              | Threshold for amount of between Track Point Observations       | No             |
| `CACHE_ENTRY_EXPIRE_SEC`           | `30 `                                                              | How long to wait for new points before creating a new Track    | No             |
| `GEOHASH_LOW`                      | `5`                                                                | Low geohash                                                    | No             |
| `GEOHASH_HIGH`                     | `7`                                                                | High geohash                                                   | No             |
| `POLL_PERIOD_SECONDS`              | `10`                                                               | How often to poll for new incoming Attributes                  | No             |
| `OPERATED_BY_IRI`                  | `http://schema.dia.mil/DefenseIntelligenceCoreOntology/operatedBy` | IRI for Operated By                                            | No             |
| `DETECT_LOITERS`                   | `True`                                                             | Toggle on/off Loiter Detection                                 | No             |
| `LOITER_MIN_TIME`                  | `900`                                                              | Minimum amount of time for a valid Loiter Event                | No             |
| `DETECT_COTRAVELS`                 | `True`                                                             | Toggle on/off Cotravel Detection                               | No             |
| `MIN_COTRAVEL_DURATION_SECONDS`    | `1200`                                                             | Minimum between Objects in a Track for a Cotravel Event        | No             |
| `MIN_LAG_LEAD_DURATION_SECONDS`    | `1200`                                                             | Minimum amount between Objects in a Track for a Lag/Lead Event | No             |
| `MAX_LAG_LEAD_DURATION_SECONDS`    | `2700`                                                             | Maximum between Objects in a Track for a Lag/Lead Event        | No             |
| `SIMILAR_TRACKS`                   | `True`                                                             | Toggle on/off Similar Track Calculations                       | No             |
| `N_TRACKS`                         | `5`                                                                | Number of similar tracks to return                             | No             |
| `WITHIN_METERS`                    | `3000.0`                                                           | Used to define the search space for potential similar tracks   | No             |
| `SQS_QUEUE_URL`                    | `http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/geoSensemakerTrigger` | SQS Queue URL                            | Yes            |


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

## Installing CoreNLP and Stanza, using the TrainingDataProcessor, and Training a CoreNLP Model

To train a custom CoreNLP model, or generate the data needed to train the model, follow the instructions in [train_corenlp_model.md].

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
[pgAdmin]: https://www.pgadmin.org/
[train_corenlp_model.md]: ./src/oms_sensemaking/nlp/docs/train_corenlp_model.md
