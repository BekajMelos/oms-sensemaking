# Integrating Sensemaking with other ATOMS services

### Steps to see Sensemaker objects with Chronicle

1. Repos needed: `chronicle-ui`, `oms-bridge`, `oms-data` (for Geospatial), `oms-sensemaking`, `oms-nlq`
2. In `oms-sensemaking`
    1. Follow the instructions in the [README](../../README.md) to copy the `.env.template` to `.env`, setup the python environment, and install dependencies.
    2. Update/confirm the `.env` file with the following values. _Please note the uncommented and commented settings_
        * `POSTGRES_PORT=5432`
        * `# RMQ_GEO_QUEUE_NAME=oms-bridge`
        * `OMSB_VERSION=<OMSB_VERSION> (eg: 3.1.4)`
        * `# OMSB_URL="https://localhost:8020/graphql"`
        * `# AAC_URL="http://aac2:3000"`
        * `RABBITMQ_HOST=rabbitmq`
    3. Run `make up`
    4. Navigate to the API at https://localhost:5001
        1. If you are having issues getting the app to load, compare your `.env` with the `.env.template`
3. In `oms-nlq`
    1. Create a `.env` file with the following contents. _Please note the `LOADING_OMS_DATA_DIR` and `LOADING_OMS_BRIDGE_DIR` environment variables_.
    ```
    # NLQ_OLLAMA_BASE_URL=http://host.docker.internal:11434
    # NLQ_LLM_MODEL=deepseek-r1:7b
    # NLQ_OMS_STRICT_DN_VALIDATION=False
    # NLQ_LOG_LEVEL=DEBUG

    NLQ_OLLAMA_SERVER_URL=http://host.docker.internal:11434
    NLQ_LLM_MODEL=deepseek-r1:14b
    NLQ_OMS_STRICT_DN_VALIDATION=False
    NLQ_LOG_LEVEL=DEBUG

    LOADING_OMS_DATA_DIR=/Users/<some username/<path to>/oms-data
    LOADING_OMS_BRIDGE_DIR=/Users/<some username>/<path to>/oms-bridge
    LOADING_OMS_AIS_DATA_PULL_DATE=2024-12-11

    LOADING_GOVERNANCE_QDRANT_API_KEY=${QDRANT__SERVICE__API_KEY}
    LOADING_GOVERNANCE_QDRANT_CA=/app/certs/all_trusted.crt
    LOADING_GOVERNANCE_QDRANT_TLS_ENABLED=${QDRANT__SERVICE__ENABLE_TLS}

    LOADING_ONTOLOGY_QDRANT_API_KEY=${QDRANT__SERVICE__API_KEY}
    LOADING_ONTOLOGY_QDRANT_CA=/app/certs/all_trusted.crt
    LOADING_ONTOLOGY_QDRANT_TLS_ENABLED=${QDRANT__SERVICE__ENABLE_TLS}

    NLQ_QDRANT_API_KEY=${QDRANT__SERVICE__API_KEY}
    NLQ_QDRANT_TLS_ENABLED=${QDRANT__SERVICE__ENABLE_TLS}
    ```
    2. Create a `.env.dev` file with the following contents. _Please note the
    `LOADING_OMS_DATA_DIR`, `LOADING_OMS_BRIDGE_DIR`, `POSTGRES_IMAGE`, `LOADING_ONTOLOGY_GIT_BASE_DIRECTORY`, `PIP_INDEX`, and `DOCKER_REGISTRY` environment variables_.
    ```
    POSTGRES_IMAGE=<Docker Registry>:5000/postgis/postgis:17-3.5
    QDRANT_IMAGE=qdrant/qdrant:v1.13.3

    NLQ_OLLAMA_SERVER_URL=http://host.docker.internal:11434
    NLQ_OLLAMA_API_PATH=/api/generate
    # NLQ_LLM_MODEL=deepseek-r1:14b
    NLQ_OMS_STRICT_DN_VALIDATION=False
    NLQ_LOG_LEVEL=DEBUG

    LOADING_ONTOLOGY_GIT_BASE_DIRECTORY=https://<Docker Registry>:3000/api/v1/repos/oms/oms-bridge/raw/etc/ontology

    PIP_INDEX=https://<Docker Registry>:3000/api/packages/oms/pypi/simple

    LOADING_OMS_DATA_DIR=/Users/davidnyman/workspace/oms-data
    LOADING_OMS_BRIDGE_DIR=/Users/davidnyman/workspace/omsb2
    LOADING_OMS_AIS_DATA_PULL_DATE=2024-12-11
    NLQ_OMS_ESS_URL=https://<Docker Registry>:30020/services/ess/3.0/es

    SERVER_OPTIONS=--reload

    DOCKER_REGISTRY=<Docker Registry>:5000

    NLQ_LLM_MODEL=mistral:instruct
    NLQ_LLM_GOV_MODEL=mistral:instruct

    NLQ_ONTOLOGY_MATCH_THRESHOLD=0.9
    NLQ_USE_CLASS_ONT_CHILDREN=True
    ```
    3. On the command line `brew install go-task`
    4. On the command line `brew install uv`
4. In `chronicle-ui`
    1. Install dependencies
    ```
    brew install nvm
    nvm install
    ```

    _Note: On MacOS systems `~/.zshrc` add the following lines_
    ```
    export NVM_DIR="$HOME/.nvm"
    [ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && \. "/opt/homebrew/opt/nvm/nvm.sh"  # This loads nvm
    [ -s "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm" ] && \. "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm"  # This loads nvm bash_completion
    ```
    2. Open a new terminal or source `~/.zshrc` check the version
        `node --version`
    3. Alias the version from the response
        `nvm alias default <version from command>`
    4. Modify the `vite.config.ts` file in the `server/proxy/'^/services/oms-bridge/2\.0/.*':` section of the json to reflect
    ```
    '^/services/oms-bridge/2\.0/.*': {
        target: 'https://localhost:8020/',
        rewrite: (path) => path.replace(/^\/services\/oms-bridge\/2\.0/, ''),
        headers: { user_dn },
        secure: false
    }
    ```
   2. Run `npm install` and `npm start`
   3. Navigate to the chronicle page at http://localhost:5173/
      1. If you have issues getting the page to load in Firefox, try a different browser or a private browser
5. In `oms-bridge`
    1. Install sdkman
        1. `curl -s "https://get.sdkman.io" | bash`
            * You may see a message after the curl install
            ```
            Please open a new terminal, or run the following in the existing one:
            source "/Users/<some username>/.sdkman/bin/sdkman-init.sh"
            ```
        2. `sdk env install`
    2. Create a `.env` and include the following. _Please note the `DOCKER_REGISTRY` environment variable_
        ```
        ######################################################################################
        ## Non Application Configuration                                                    ##
        ######################################################################################
        COMPOSE_PROFILES=
        ATOMS_VERSION=3.1.4
        DOCKER_REGISTRY=<Docker Registry>:5000
        COMPOSE_PROFILES=remote
        DOCKER_PREFIX=aio4/dev/services/oms
        MEME_WHITELIST="CN: oms.apps.dev.dpaas.dodiis.mil|CN: oms.apps.dev.dpaas.dodiis.mil,OU: DIA,OU: DoD,O: U.S. Government,C: US|CN: omsserver,OU: oms,O: blackcape,L: arlington,ST: virginia, C: us"
        GRAPHQL_ENDPOINT=https://oms.apps.dev.dpaas.dodiis.mil/services/oms/3.0/
        OMSB_CONFIGFILE_BUCKET=
        MAX_RAM_PERCENTAGE=70.0
        INITIAL_RAM_PERCENTAGE=50.0

        ######################################################################################
        ## Integration test variables                                                       ##
        ######################################################################################
        OMSB_TEST_MAILPIT_URL=http://localhost:8025/

        UVICORN_SSL_KEYFILE=/opt/common/pki/server.private
        UVICORN_SSL_CERTFILE=/opt/common/pki/server.public
        UVICORN_SSL_CERT_REQS=0
        UVICORN_PORT=8843
        UVICORN_ROOT_PATH=
        ```
6. In oms-data
    1. Create a `.env` file with the following contents:
    ```
    DOCKER_REGISTRY=<Docker Registry>
    ```
    2. Install dependencies
    ```
    brew install poetry
    make install
    ```
7. Trigger Sensemaker execution
    1. In `oms-nlq` run `task load-oms-data`
