# Packaging & Versioning

## Building the *OMS Sensemaking* project

To package the project for distribution:

```
make build
```

This command will build a Python wheel as well as an archive of the source code
and store the results in the *dist* directory.

> ***NOTE***: The project version is determined dynamically based on the
> project's git repository using [setuptools-scm].


## Building Project Documentation

1. Install documentation dependencies

    ```
    pip install -e ".[docs]"
    ```

2. Build the documentation site

    ```
    mkdocs build
    ```

3. Package documentation site as a tarball

    ```
    mkdir -p dist
    ```

The resulting static site files can be found in the `site` directory, which can
be packaged and deployed to a server or browsed locally.

> ***TIP***: Alternatively you can host a local copy of the docs with `mkdocs serve`

## Building the Docker Image

The Docker image is intended to be used in two separate contexts: in development
as part of a *docker compose* environment and as a standalone image that can be
deployed in other environments.

The project version number is determined dynamically based on Git tags. Since
the local `.git` directory is excluded from the Docker image, the application's
version needs to be provided as a build argument. This circumvents the automatic
detection of the version number during the image build process.

To Build the OMS Sensemaking Docker Image:

1. Ensure you have a local virtual environment (e.g. `.venv`)

    See the [Development Environment] documentation for how to set this up.

2. Ensure you have a `.netrc` filed configured

    See the [Development Environment] documentation for how to set this up.

3. Use `docker build` to build the image

    ```
    VENV_DIR="${VENV_DIR:-.venv}"
    APP_VERSION=$(source $VENV_DIR/bin/activate && python -m setuptools_scm)

    docker build \
    --build-arg $APP_VERSION \
    --no-cache \
    -t oms_sensemaking:latest \
    --secret id=mynetrc,src=${HOME}/.netrc
    .
    ```

## Versioning *OMS Sensemaking*

*OMS Sensemaking* leverages [setuptools-scm] for dynamic versioning based on Git tags.

To cut new release:

1. Create a Git tag with the semantic version number

    The format for the git tag is `MAJOR.MINOR.PATCH`.

        git checkout main
        git pull
        git tag -a -m 'Release 1.2.3 (Galadriel-INC-1)' 1.2.3
        git push origin tag 1.2.3

2. (optional) Create build artifacts

    If you opt to include build artifacts, you will have to build them offline
    and upload them to the release page, since there is currently no Continuous
    Integration process in the Tex environment.

    - Checkout the Git tag for the release

        ```
        git checkout 1.2.3
        ```

    - Build the project

        ```
        make distclean build
        ```

3. Create a *release* page

    - Navigate to the tags section of the repo and location the tag you just created

    - Click the *New Release* link

    - Add a description of the release and include any relevant notes about
      what changed since the previous release.

    - (optional) If you created build artifacts, upload them and optionally
      reference them in the release notes.

## Releasing a new Version
1. Update the changelog
    - User facing updates only and remember to update links at the bottom
2. Create a git tag
    - Follow [Versioning Instructions](#versioning-oms-sensemaking) to create tag
3. Run the sync job locally
    - Clone the Devops/sync-artifacts repo
    - Install the `aws` cli https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
    - (optional) Update `respositories.csv` to just include the repos you care about
    - Ask teammate for `~/.aws/credentials` file
    - Run `make clean bundle upload`
4. Run the sync job in AIDE Jenkins
    - Navigate to AIO4/Apps/oms/sync-all-repos
    - Build with parameters
    - You can double check in gitlab that the latest commits and tags are created
5. Build the sensemaking docker image in AIDE Jenkins
    - Navigate to AIO4/Apps/oms/oms-sensemaking-docker
    - Switch to the tags instead of the branches, then do a “Scan Multi Branch Pipeline” to pick up the new tag
    - Refresh and go into the Tag and build with default params
    - Wait for successful build
6. (optional) Check Artifactory and Sonarqube
    - Check Artifactory for the image
    - Check Sonarqube for the scans to have run on the images


[setuptools-scm]: https://setuptools-scm.readthedocs.io
[Development Environment]: dev.md
