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

## Versioning *OMS Sensemaking*

*OMS Sensemaking* leverages [setuptools-scm] for dynamic versioning based on Git tags.

To cut new release:

1. Create a Git tag with the semantic version number

    The format for the git tag is `vMAJOR.MINOR.PATCH`.

        git checkout main
        git tag -a -m 'Release 1.2.3' v1.2.3
        git push
        git push --tags

2. (optional) Create build artifacts

    If you opt to include build artifacts, you will have to build them offline
    and upload them to the release page, since there is currently no Continuous
    Integration process in the Tex environment.

    - Checkout the Git tag for the release

        ```
        git checkout v1.2.3
        ```

    - Build the project

        ```
        make distclean build
        ```

3. Create a *release* page in Gitea

    - Navigate to the tags section of the repo and location the tag you just created

        For example `https://tex.gerbil-cloud.ts.net:3000/oms/oms-sensemaking/releases/new?tag=v1.2.3`

    - Click the *New Release* link

    - Add a description of the release and include any relevant notes about
      what changed since the previous release.

    - (optional) If you created build artifacts, upload them and optionally
      reference them in the release notes.

[setuptools-scm]: https://setuptools-scm.readthedocs.io
