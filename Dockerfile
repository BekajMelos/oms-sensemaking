# syntax=docker/dockerfile:1
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

ARG PIP_INSTALL='pip install --no-cache-dir'

ENV MODULE_NAME=src.oms_sensemaking.service

# dump the Python traceback for segfaults and other signals
ENV PYTHONFAULTHANDLER=1

# disable bytecode generation
ENV PYTHONDONTWRITEBYTECODE=1

# Force stdout & stderr streams to be unbuffered
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . /app

RUN --mount=type=secret,id=mynetrc,dst=/root/.netrc,mode=0600 apt-get update && \
    apt-get install -y --no-install-recommends apt-utils ca-certificates git gzip tar && \
    $PIP_INSTALL --upgrade pip wheel && \
    pip install . && \
    apt-get purge -y apt-utils git && \
    apt-get clean -y && \
    apt-get autoclean -y && \
    apt-get autoremove -y
