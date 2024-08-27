#!/bin/bash
#
# This is a helper script for the localstack environment to install
# the needed system dependencies to run our bootstrap script.

apt update
apt install -y gettext jq
apt-get install gettext-base