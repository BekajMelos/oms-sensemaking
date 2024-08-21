# syntax=docker/dockerfile:1
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

ARG PIP_INSTALL='pip install --no-cache-dir'

ENV MODULE_NAME=oms_sensemaking.service

# dump the Python traceback for segfaults and other signals
ENV PYTHONFAULTHANDLER=1

# disable bytecode generation
ENV PYTHONDONTWRITEBYTECODE=1

# force stdout & stderr streams to be unbuffered
ENV PYTHONUNBUFFERED=1

# account for src layout
ENV PYTHONPATH=/app/src

WORKDIR /app

COPY . /app

# - mount .netrc as a Docker secret
# - install packages to support installing git based Python dependencies (e.g. git)
# - install packages to support installation of postgresql client libraries
# - install Python dependencies
# - clean up
RUN --mount=type=secret,id=mynetrc,dst=/root/.netrc,required,mode=0600 apt-get update && \
    apt-get install -y --no-install-recommends apt-utils ca-certificates curl git gzip tar lsb-release && \
    install -d /usr/share/postgresql-common/pgdg && \
    curl -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc --fail https://www.postgresql.org/media/keys/ACCC4CF8.asc && \
    echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
    apt-get update && \
    apt-get install -y postgresql-client-16 && \
    $PIP_INSTALL --upgrade pip wheel && \
    pip install . && \
    apt-get purge -y apt-utils curl git && \
    apt-get clean -y && \
    apt-get autoclean -y && \
    apt-get autoremove -y
