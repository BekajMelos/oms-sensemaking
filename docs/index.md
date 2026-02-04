# ATOMS Sensemaking

## Project layout

    src/oms_sensemaking         # The top-level package
    src/oms_sensemaking/core    # shared components
    src/oms_sensemaking/models  # ORM models
    docs/
        index.md                # The documentation homepage.
        ...                     # Other markdown pages, images and other files.
    migrations/                 # database schema migrations

## Quickstart

> Assumes you are using the *atoms-sensemaking* Docker environment.

1. Create a minimal .env file

        # .env --- Local configuration.
        #
        # ----------------------------------------
        # Sensemaker Database
        # ----------------------------------------
        POSTGRES_USER=postgres
        POSTGRES_PASSWORD=password

        # ----------------------------------------
        # ATOMS SDK Settings
        # ----------------------------------------
        OMSB_URL="https://localhost:8020/graphql"
        OMSB_VERSION=3.1.4
        CERT_PATH=./etc/pki/test10.pem
        KEY_PATH=./etc/pki/test10.key

2. Start the ATOMS Sensemaking Docker environment

        docker compose up -d

    This will start the ATOMS Sensemaking service on port 5001. The REST API
    docs can be found [here].

    > To stop the ATOMS Sensemaking Docker environment, run `docker compose down`

[here]: https://localhost:5001/docs