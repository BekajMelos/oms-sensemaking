# Contributing to oms-sensemaking

Contributions to *oms-sensemaking* are welcome! If you find a bug or have an
idea for enhancements, please report them through the [Jira] or reach out to
oms-sensemaking team to create a ticket on your behalf. Changes should be
submitted as a pull request.

## Getting Started

Consider reviewing the [README](./README.md) for information how to set up your
development environment as well as more information on the different components
of oms-sensemaking.

## Workflow

The following denotes the typical workflow to follow when making contributions
to *oms-sensemaking*.

### Tracking Work

All works should be associated with a an issue in the [ticket tracker]. There
are several templates that can be used depending on the type of issue:

- [New Feature](./.gitea/issue_template/New Feature.md)
- [Enhancement or Refactor](./.gitea/issue_template/Enhancement or Refactor.md)
- [Bug](./.gitea/issue_template/Bug.md)


### Making Changes

- Create a topic branch for your work

  + This branch should typically be branched from *main*

  + Ensure that the branch has a name in the format:
    `{fix|feature}/{prefix}-{ticket number}_{optional short description}`

    For example:

    ```sh
    git checkout -b feature/FOO-123_short-description
    ```

- Make your changes

- Verify that your changes adhere to our code compliance guidelines

  + Run `make lint`

    - Ensure docker containers are running

- Ensure unit tests are passing

  + Run `make up test`

- Commit your changes

  + Use the following format for commit messages:

    - Short description (50 characters or less).

      + Detailed description, if neccessary, preceded with a blank line. Wrap
        the detailed description at 72 characters. The blank line separates the
        short description from the longer description allowing for better
        integration with a variety of tools (e.g. `git log --oneline`).

      + See [How to Write a Git Commit Message] for more tips on how to write
        commit messages.

### Submitting Changes For Review

- Push your topic branch to Gitea

- Submit a Pull Request

  + Use the [Pull Request Template](./.gitlab/Pull Request Template.md)

  + Include a detailed description of how to test the changes

  + Include the ticket number and/or a link to the ticket

  + Include test steps for verifying the changes

- Gather feedback through Gitea's [Pull Requests] feature


### Reviewing Pull Requests

- Checkout the topic branch

- Follow the test instructions provided in the pull request

- Use Gitea to comment on the merge request if you have any questions or
  concerns

- Use your best judgement before approving merge requests

  + If you are satisfied with the changes, add your stamp of approval.

    You can do this by clicking the *approve* button on the pull requests.

### Merging Pull Requests

The author of the Pull Request should be responsible for merging, once there is
an approval.

If Gitea can handle the merge automatically, you will be presented with options
for what type of merge commit you would like to create. In addition to selecting
the type of merge commit to use, you may also be presented with the option to
delete the the branch once merged, which is recommended.

In the event their are outstanding conflicts, the author of the pull request
will be resonsible for resolving them.


[How to Write a Git Commit Message]: https://chris.beams.io/posts/git-commit/
[Ticket Tracker]: https://jira.code.dodiis.mil
[Pull Requests]: https://tex.gerbil-cloud.ts.net:3000/oms/oms-sensemaking/pulls/
