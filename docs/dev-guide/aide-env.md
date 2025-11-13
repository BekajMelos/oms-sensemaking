# AIDE Environment

This is an example setup that should work in AIDE with appropriate
settings set for `<>`. Seek guidance from teammates for other envs.

## Setup

In AIDE assuming the virtual environment is setup as follows:

```shell
python -m venv /tmp/venv
source /tmp/venv/bin/activate
```
## .netrc

Contents of `~/.netrc`:

```
machine artifactory.code.dodiis.mil
login <service-account-user>
password <service-account-password>
```

## pip.conf

Contents of `/tmp/venv/pip.conf`

```
[global]
index-url = <artifact-url>/api/pypi/pypi/simple
trusted-host = artifactory.code.dodiis.mil
```
