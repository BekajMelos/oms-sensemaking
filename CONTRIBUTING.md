# Contributing to atoms-sensemaking

Contributions to *atoms-sensemaking* are welcome! If you find a bug or have an
idea for enhancements, please reach out to
atoms-sensemaking team to create a ticket on your behalf. Changes should be
submitted as a pull request.

## Getting Started

Consider reviewing the [README](./README.md) for information on the different components of atoms-sensemaking and setting up pre-requisites.

## Development Environment

Ask a teammate for supplemental references to:

- Setup additional variables in `.env`.
- Configure Access Tokens in `~/.netrc`.
- Configure pip to use a private PyPI in `.venv/pip.conf`.

### Environment Variables

> See [Environment Settings](./docs/dev-guide/env-vars.md) for a full list of environment variables that can be configured.

At a minimum, you will need to set the below variables. Others may rely on the default values set in the
application's configuration.

| Variable Name       | Example                                          |                      Description                       |
|:--------------------|:-------------------------------------------------|:------------------------------------------------------:|
| `POSTGRES_PASSWORD` | `xxxxxxx`                                        |      The password for the PostgreSQL admmin user       |
| `OMSB_VERSION`      | `3.1.6`                                          |               The version of Atoms Core                |
| `OMSB_URL`          | `https://localhost:8020/graphql`                 |                      URL for OMSB                      |
| `CERT_PATH`         | `./etc/pki/test10.pem`                           |                    Path to User PEM                    |
| `KEY_PATH`          | `./etc/pki/test10.key`                           |                    Path to User Key                    |
| `ATOMS_CACERT_PATH` | `./etc/pki/trusted.crt`                          |   Path to CA File used for your local dev containers   |
| `DOCKER_REGISTRY`   | `hostname:5000`                                  |      Socket address of the remote docker registry      |
| `PIP_INDEX`         | `https://host:3000/api/packages/oms/pypi/simple` |             URL for the private pip index              |
| `ATOMS_LOCAL_DEV`   | `../atoms-local-dev`                             |            Path to the atoms-local-dev repo            |

### Common Development Workflow

#### Services

- Start services: `make up`
- Stop services: `make down`

#### Manage containers

- Remove volumes: `make nuke`
- Remove volumes, rebuild containers with updated dependencies: `make refresh`

## Workflow

The following denotes the typical workflow to follow when making contributions
to *atoms-sensemaking*.

### Tracking Work

Ask a teammate for guidance.


### Making Changes

- Create a topic branch for your work

  + This branch should typically be branched from *main*

  + Ensure that the branch has a name in the format:
    `SM-{ticket number}-{optional short description}`

    For example:

    ```sh
    git switch -c SM-123-short-description
    ```

- Make your changes

- Verify code quality

  + Run `make fix`
  + Rune `make format`

- Verify that your changes adhere to our code compliance guidelines

  + Run `make lint`

    - Ensure docker containers are running

- Ensure unit tests are passing

  + Run `make up test`

- API Testing (Postman)

  + In [Postman](https://www.postman.com/downloads/), "Import" the [postman](../../postman) directory. Use the `Sensemaking ATOMS Localhost` environment while running the `Sensemaking Smoke Tests`.

- Commit your changes

  + Use the following format for commit messages:

    - Short description (50 characters or less).

      + Detailed description, if necessary, preceded with a blank line. Wrap
        the detailed description at 72 characters. The blank line separates the
        short description from the longer description allowing for better
        integration with a variety of tools (e.g. `git log --oneline`).

      + See [How to Write a Git Commit Message] for more tips on how to write
        commit messages.

      + Create a [CHANGELOG](./CHANGELOG.md) entry for your changes 

### Submitting Changes For Review

Ask a teammate for guidance.

### Reviewing Pull Requests

- Checkout the topic branch

- Follow the test instructions provided in the pull request

- Comment on the merge request if you have any questions or
  concerns

  - When the Developer responsible for the Pull Request has responded
    adequately the Commenter should mark the conversation as resolved;
    Devs should not resolve comments themselves unless they are trivial
    or the Commenter **clearly** considers the matter resolved.

- Use your best judgment before approving merge requests

  + If you are satisfied with the changes, add your stamp of approval.

    You can do this by clicking the *approve* button on the pull requests.

### Merging Pull Requests

The author of the Pull Request should be responsible for merging, once there are
**two** approvals.

If the merge can succeed automatically, you will be presented with options
for what type of merge commit you would like to create. In addition to selecting
the type of merge commit to use, you may also be presented with the option to
delete the branch once merged, which is recommended.

In the event there are outstanding conflicts, the author of the pull request
will be responsible for resolving them.


[How to Write a Git Commit Message]: https://chris.beams.io/posts/git-commit/
[Pull Requests]: Repository for atoms-sensemaking

## Utilities

See the [scripts](./scripts) directory for various developer utilities.

- [Load Testing & Queue Performance Metrics](./docs/dev-guide/load-test.md)