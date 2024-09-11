# syntax=docker/dockerfile:1
#
# This Dockerfile provides a multi-stage build for an Alpine based image with
# Python 3. The first build stage sets up Alpine and Python 3, while the second
# build stage installs the application and it's dependencies.
#
# The base image can be configured through the following build arguments:
#
#   ALPLINE_VARIANT: The image name for the alpine variant to use. Defaults to
#                    "alpine".
#
#   ALPINE_VERSION:  The version of alpine to use. Defaults to 3.19.3
#
#   DOCKER_PROXY:    The prefix for the docker repository where the base image is
#                    hosted. This should end in a forward slash. Defaults to
#                    docker.io/library
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
# - Swap base image with one of the DPaaS images
# - oms_sdk dependency is handled differently in Tex vs AIDE, but the details are not clear yet
ARG ALPINE_VARIANT="alpine"

ARG ALPINE_VERSION="3.20.2"

# The docker image prefix. This should end in a forward slash (i.e. /).
ARG DOCKER_PROXY="docker.io/library"

FROM ${DOCKER_PROXY}/${ALPINE_VARIANT}:${ALPINE_VERSION} AS python-base

# NOTE: Permissions are handled at the group level. The user created here is
#       used as a default, but in production the actual user id may vary and
#       could possibly not be known ahead of running the image.
ARG USER_NAME=appuser

ARG GROUP_NAME=${USER_NAME}

ARG VENVS_DIR=/opt/virtualenvs

ENV APP_HOME=/app

ENV LANG=C.UTF-8

LABEL maintainer="OMS Team <oms@blackcape.io>"

WORKDIR ${APP_HOME}

RUN <<EOF
# create user and group
addgroup $GROUP_NAME
adduser \
  --disabled-password \
  --gecos "Application user" \
  --home "$APP_HOME" \
  --no-create-home \
  --ingroup "$GROUP_NAME" \
  $USER_NAME

# configure package manager
apk update
apk upgrade

# install core system dependencies
apk add --no-cache \
  bash \
  python3 \
  py3-pip \
  py3-wheel

# prepare file system
mkdir -p $APP_HOME $VENVS_DIR
chown $USER_NAME:$GROUP_NAME $APP_HOME $VENVS_DIR
chmod 774 $APP_HOME $VENVS_DIR

# clean up
rm -rf /var/cache/apk/*
EOF


FROM python-base AS app

ARG APP_VERSION="0.0.0"

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
#       for a PEP5O8 Git URL to be used to define a dependency on the oms_sdk
#       project. This exists because there is no infrastructure for hosting
#       custom dependencies in the development environment.
RUN --mount=type=secret,id=mynetrc,dst=/root/.netrc,required,mode=0600 <<EOF
# configure package manager
apk update
apk upgrade

# install application's system dependencies
apk add --no-cache geos postgresql-client

# initialize virtual environment
python3 -m venv --prompt app $VENVS_DIR/app
source $VENVS_DIR/app/bin/activate
pip install --upgrade pip wheel

# prepare build dependencies
apk add --no-cache --virtual .build-deps \
  gcc \
  geos-dev \
  git \
  musl-dev \
  python3-dev

# install app
pip install .

# configure app
mv $APP_HOME/docker/start.sh /
chmod 755 /start.sh

# contrib
APP_SHORT_NAME=oms_sensemaking
mkdir -p /usr/share/doc/$APP_SHORT_NAME/contrib
alembic upgrade head --sql > /usr/share/doc/$APP_SHORT_NAME/contrib/$APP_SHORT_NAME-schema.sql

# configure extras
apk add --no-cache --virtual .extra-deps curl figlet
curl -o /usr/share/figlet/fonts/graffiti.flf http://www.figlet.org/fonts/graffiti.flf
chmod 644 /usr/share/figlet/fonts/graffiti.flf
mv /etc/motd /etc/motd-alpine
figlet -w 90 -f graffiti "OMS SenseMaking" > /etc/motd
rm /usr/share/figlet/fonts/graffiti.flf

# cleanup
apk del .build-deps .extra-deps
rm -rf /var/cache/apk/*
EOF

CMD ["/start.sh"]
ENTRYPOINT ["/entrypoint.sh"]
