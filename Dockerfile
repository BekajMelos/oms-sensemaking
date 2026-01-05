# This Dockerfile provides a multi-stage build for a UBI8 based image with
# Python 3.12. The first build stage sets up UBI8 and Python 3.12, while the second
# build stage installs the application and it's dependencies.
#
# The base image can be configured through the following build arguments:
#
#   PUBLISHER:       The publisher of the image. Redhat
#
#   IMAGE_BASE:      The image base. UBI8
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

ARG NAMESPACE="redhat"

ARG IMAGE_NAME="ubi8"

ARG IMAGE_VERSION="latest"

# The paramterized base image.
FROM ${NAMESPACE}/${IMAGE_NAME}:${IMAGE_VERSION} AS python-base

# NOTE: Permissions are handled at the group level. The user created here is
#       used as a default, but in production the actual user id may vary and
#       could possibly not be known ahead of running the image.
ARG USER_NAME=appuser

ARG GROUP_NAME="${GROUP_NAME:-$USER_NAME}"

ARG VENVS_DIR=/opt/virtualenvs

ENV APP_HOME=/app

ENV LANG=C.UTF-8

LABEL maintainer="OMS Team <oms@blackcape.io>"

WORKDIR ${APP_HOME}

ENV PYTHON_VERSION="3.12.10"

USER root
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
dnf install -y \
  ca-certificates \
  curl \
  gzip \
  tar

dnf install -y python3.12 python3.12-pip
pip3 uninstall setuptools -y
rm -f /usr/local/bin/pip /usr/local/bin/pip3 || true
alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 100 \
&& alternatives --install /usr/bin/pip pip /usr/bin/pip3.12 100 \
&& alternatives --set python3 /usr/bin/python3.12 \
&& alternatives --set pip /usr/bin/pip3.12

# prepare file system
mkdir -p $APP_HOME
chown $USER_NAME:$GROUP_NAME $APP_HOME
chmod 774 $APP_HOME

# clean up os packages
dnf clean all
update-ca-trust
EOF

FROM python-base AS app

ARG APP_VERSION="0.0.0"

ARG BUILD_DATE

ARG VCS_REF

ARG PIP_INDEX_URL

ARG PIP_EXTRA_INDEX_URL

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

ENV UVICORN_HOST=${UVICORN_HOST:-${HOST:-0.0.0.0}}

ENV UVICORN_PORT=${UVICORN_PORT:-${PORT:-8443}}

ENV UVICORN_ROOT_PATH=${UVICORN_ROOT_PATH:-}

COPY --chown=appuser:appuser migrations ${APP_HOME}/migrations
COPY --chown=appuser:appuser src ${APP_HOME}/src
COPY --chown=appuser:appuser data ${APP_HOME}/data
COPY --chown=appuser:appuser src/oms_sensemaking/templates ${APP_HOME}/src/oms_sensemaking/templates
COPY --chown=appuser:appuser --chmod=644 alembic.ini pyproject.toml README.md ${APP_HOME}
COPY --chown=appuser:appuser --chmod=755 prestart.sh ${APP_HOME}
COPY --chown=appuser:appuser --chmod=755 docker/start.sh docker/healthcheck.sh /
COPY --chmod=644 docker/banner.txt /etc/motd

# NOTE: This RUN command is mounting a .netrc file as a Docker secret to allow
#       for a private PyPI to be used to define a dependency on the oms_sdk
#       project.
USER root
RUN --mount=type=secret,id=mynetrc,dst=/root/.netrc,required,mode=0600 \
  --mount=type=secret,id=cacert,dst=/root/ca-certificate.crt,mode=0600 <<EOF
set -e

find /app -type f ! -name '*.sh' -exec chmod 644 {} \;
find /app -type d -exec chmod 755 {} \;

# use the provided ca certificate bundle if available
if [ -f /root/ca-certificate.crt ]; then
  cp /root/ca-certificate.crt /etc/ssl/certs/ca-certificates.crt
fi

# update core Python packaging tools
export PIP_NO_INPUT=1
python3 -m pip install --upgrade pip wheel setuptools

# install application's system dependencies
dnf install -y \
  curl \
  git \
  jq \
  gcc \
  python3.12-devel \
  procps-ng

# install app
pip install .

# contrib
APP_SHORT_NAME=oms_sensemaking
mkdir -p /usr/share/doc/$APP_SHORT_NAME/contrib
alembic upgrade head --sql | gzip > /usr/share/doc/$APP_SHORT_NAME/contrib/$APP_SHORT_NAME-schema.sql.gz

# clean up os packages
dnf remove -y gcc python3.12-devel emac-filesystem oniguruma && \
dnf autoremove -y && \
dnf clean all

# remove old python packages (prisma)
rm -rf /usr/lib/python3.6/site-packages/urllib3*
rm -rf /usr/lib/python3.6/site-packages/setuptools*

# delete private keys in documentation (prisma)
rm /usr/share/doc/perl-IO-Socket-SSL/certs/*
rm /usr/share/doc/perl-Net-SSLeay/examples/*.pem

rm -rf /usr/lib/python3.12/site-packages/pip*
rm -rf /usr/lib/python6/site-packages/pip*
rm -rf /usr/bin/pip*
rm -rf /usr/local/bin/pip*
rm -rf /usr/local/lib/python3.12/site-packages/pip*

dnf remove -y tar

EOF

LABEL maintainer="The OMS Team <oms@blackcape.io>"
LABEL org.label-schema.build-date=${BUILD_DATE}
LABEL org.label-schema.name="oms-sensemaking"
LABEL org.label-schema.description="Docker image for oms-sensemaking"
LABEL org.label-schema.vcs-url="https://gitlab.code.dodiis.mil/aio4/services/omsbridge/oms-sensemaking"
LABEL org.label-schema.vcs-ref=${VCS_REF}
LABEL org.label-schema.version=${APP_VERSION}

USER ${USER_NAME}
CMD ["/start.sh"]
