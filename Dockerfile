# syntax=docker/dockerfile:1
#
# This Dockerfile provides a multi-stage build for a Debian based image with
# Python 3. The first build stage sets up Debian and Python 3, while the second
# build stage installs the application and it's dependencies.
#
# The base image can be configured through the following build arguments:
#
#   IMAGE_NAME:      The image name of the base image. Defaults to "python".
#
#   PYTHON_VERSION:  The version of Python to use. Defaults to "3.12.6".
#
#   DOCKER_PROXY:    The prefix for the docker repository where the base image is
#                    hosted. This should end in a forward slash. Defaults to
#                    "docker.io/library".
#
# The application is installed in $APP_HOME, which defaults to /app. A virtual
# environment will be created for the application in /opt/virtualenvs/app. This
# virtual envrionment needs to activated either by the CMD or by an ENTRYPOINT
# that wraps a CMD.
#
# OMS Sensemaking
# ===============
# The oms-sensemaking service is configured with a startup script in
# /script.sh. This script is responsible for activating the virtual environment
# and starting the service with uvicorn. The following environment variables can
# be used to customize how the service is run.
#
#   HOST:       The hostname or ip to listen for connections on. Defaults to 0.0.0.0
#
#   PORT:       The port to listen to connections on. Defaults to 80
#
#   LOG_LEVEL:  The log level. Defaults to "INFO"
#
#   APP_MODULE: The ASGI application to run, in the format "<module>:<attribute>".
#               Defaults to "oms_sensemaking.service:app"
#
#   RELOAD_APP: A flag to enable application reloading when set to a non-empty
#               value. This is useful for quick redeployments during development.
#
# Known Issues
# ============
# - oms_sdk dependency is handled differently in Tex vs AIDE, but the details
#   for how to handle this difference are not clear.

# The name of the Docker image.
ARG IMAGE_NAME="python"

# The version of Python to use.
ARG PYTHON_VERSION="3.12.6"

# The docker image prefix.
ARG DOCKER_PROXY="docker.io/library"

# The paramterized base image.
FROM ${DOCKER_PROXY}/${IMAGE_NAME}:${PYTHON_VERSION}-slim AS python-base

# NOTE: Permissions are handled at the group level. The user created here is
#       used as a default, but in production the actual user id may vary and
#       could possibly not be known ahead of running the image.
ARG USER_NAME=appuser

ARG GROUP_NAME=${GROUP_NAME:-USER_NAME}

ARG VENVS_DIR=/opt/virtualenvs

ENV APP_HOME=/app

ENV LANG=C.UTF-8

LABEL maintainer="OMS Team <oms@blackcape.io>"

WORKDIR ${APP_HOME}

RUN <<EOF
set -e

# create group and unprivileged user
groupadd $GROUP_NAME

useradd \
  --create-home \
  --shell /bin/bash \
  --gid $GROUP_NAME \
  $USER_NAME

# install core dependencies
apt-get update
apt-get install -y --no-install-recommends \
  ca-certificates \
  curl \
  gzip \
  tar \
  lsb-release

install -d /usr/share/postgresql-common/pgdg
curl -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc --fail https://www.postgresql.org/media/keys/ACCC4CF8.asc
echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list

apt-get update
apt-get install -y --no-install-recommends postgresql-client-16

# prepare file system
mkdir -p $APP_HOME
chown $USER_NAME:$GROUP_NAME $APP_HOME
chmod 774 $APP_HOME

# clean up os packages
apt-get purge -y curl
apt-get clean -y
apt-get autoclean -y
apt-get autoremove -y
EOF


FROM python-base AS app

ARG APP_VERSION="0.0.0"

# default to private PyPI
ARG PIP_INDEX_URL="https://tex.gerbil-cloud.ts.net:3000/api/packages/oms/pypi/simple"

# fallback to public PyPI
ARG PIP_EXTRA_INDEX_URL="https://pypi.org/simple"

# disable pip cache
ARG PIP_NO_CACHE_DIR=1

# disable pip's progress bar
ARG PIP_PROGRESS_BAR=off

ARG SETUPTOOLS_SCM_PRETEND_VERSION_FOR_OMS_SENSEMAKING=${APP_VERSION}

ENV MODULE_NAME=oms_sensemaking.service

# dump the Python traceback for segfaults and other signals
ENV PYTHONFAULTHANDLER=1

# disable bytecode generation
ENV PYTHONDONTWRITEBYTECODE=1

# force stdout & stderr streams to be unbuffered
ENV PYTHONUNBUFFERED=1

# oms-sensemkaing is using the "src layout" project structure. The PYTHONPATH
# environment variable needs to be set to account for this project structure
# and ensure the application is available to the Python interpreter.
# https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/
ENV PYTHONPATH=${APP_HOME}/src

COPY . ${APP_HOME}

# NOTE: This RUN command is mounting a .netrc file as a Docker secret to allow
#       for a private PyPI to be used to define a dependency on the oms_sdk
#       project.
RUN --mount=type=secret,id=mynetrc,dst=/root/.netrc,required,mode=0600 <<EOF
set -e

# configure package manager
apt-get update

# update core Python packaging tools
python3 -m pip install --upgrade --no-cache pip wheel

# install application's system dependencies
apt-get install -y --no-install-recommends \
  curl \
  git \
  jq

# prepare build dependencies
BUILD_DEPS="gcc libgeos-dev python3-dev"
apt-get install -y --no-install-recommends $BUILD_DEPS

# install app
pip install .

# configure app
mv $APP_HOME/docker/*.sh /
chmod 755 /start.sh /healthcheck.sh

# contrib
APP_SHORT_NAME=oms_sensemaking
mkdir -p /usr/share/doc/$APP_SHORT_NAME/contrib
alembic upgrade head --sql | gzip > /usr/share/doc/$APP_SHORT_NAME/contrib/$APP_SHORT_NAME-schema.sql.gz

# configure extras
mv /etc/motd /etc/motd-alpine
mv $APP_HOME/docker/banner.txt /etc/motd
chmod 644 /etc/motd

# clean up os packages
apt-get purge -y $BUILD_DEPS
apt-get clean -y
apt-get autoclean -y
apt-get autoremove -y
EOF

LABEL maintainer="The OMS Team <oms@blackcape.io>"
LABEL org.label-schema.build-date=${APP_DATE}
LABEL org.label-schema.name="oms-sensemaking"
LABEL org.label-schema.description="docker image for oms-sensemaking"
LABEL org.label-schema.vcs-url="https://gitlab.code.dodiis.mil/aio4/services/omsbridge/oms-sensemaking"
LABEL org.label-schema.vcs-ref=${VCS_REF}
LABEL org.label-schema.version=${APP_VERSION}

USER ${USER_NAME}
CMD ["/start.sh"]
