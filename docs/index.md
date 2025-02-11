# OMS Sensemaking

## Project layout

    src/oms_sensemaking         # The top-level package
    src/oms_sensemaking/core    # shared components
    src/oms_sensemaking/models  # ORM models
    docs/
        index.md                # The documentation homepage.
        ...                     # Other markdown pages, images and other files.
    migrations/                 # database schema migrations

## Quickstart

> Assumes you are using the *oms-sensemaking* Docker environment.

1. Create a minimal .env file

        # .env --- Local configuration.
        #
        # ----------------------------------------
        # Sensemaker Database
        # ----------------------------------------
        POSTGRES_PASSWORD=password
        PGPASSWORD=password

        # ----------------------------------------
        # OMS SDK Settings
        # ----------------------------------------
        OMSB_URL="https://localhost:8020/graphql"
        OMSB_VERSION=Grimlock-INC-12
        CERT_PATH=./etc/pki/test10.pem
        KEY_PATH=./etc/pki/test10.key

2. Start the OMS Sensemaking Docker environment

        docker compose up -d

    This will start the OMS Sensemaking service on port 5001. The REST API
    docs can be found [here].

    > To stop the OMS Sensemaking Docker environment, run `docker compose down`

Alternatively, there is also a [command line interface] to the individual
sensemaker categories.

[here]: https://localhost:5001/docs
[command line interface]: dev-guide/cli.md
