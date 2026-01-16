# Integrating Sensemaking with other ATOMS services

### Steps to see Sensemaker objects with Chronicle

1. Repos needed: `chronicle-ui`, `oms-bridge`, `oms-data-gen` (for Geospatial), `oms-sensemaking`
2. In `oms-sensemaking`
    1. Deteremine your IP address: `ipconfig getifaddr en0`
    2. Update the `.env` with the following values. _Please note the uncommented and commented settings_
        * `# POSTGRES_PORT=5432`
        * `RMQ_GEO_QUEUE_NAME=oms-wfs-trigger`
        * `OMSB_VERSION=<OMSB_VERSION>`
        * `OMSB_URL="https://<your_ip_address>:8443/graphql"`
        * `AAC_URL="http://<your_ip_address>:5022"`
        * `RABBITMQ_HOST=<your_ip_address>`
    3. Set the sensemaker RMQ queue name. `oms-bridge` does not support all of our RMQ Queues, so only one sensemaker can be used at a time at the moment.
        1. Update the `.env` to set the RMQ queue to the `oms-wfs-trigger` (we're temporarily using that queue)
            * Set the appropriate RMQ_<sensemaker>_QUEUE_NAME to the `oms-wfs-trigger`
            * QUEUE Settings are `RMQ_GEO_QUEUE_NAME`, `RMQ_INFERENCE_QUEUE_NAME`, `RMQ_RES_QUEUE_NAME`, `RMQ_MIL_SYMBOL_QUEUE_NAME`
            * Example for the Geo sensemakers: `RMQ_GEO_QUEUE_NAME=oms-wfs-trigger`
    4. Run `docker compose up -d`
    5. Navigate to the API at https://localhost:5001/docs
        1. If you are having issues getting the app to load, compare your `.env` with the `.env.template`
3. In `chronicle-ui`
   1. Follow the chronicle _Setup_ steps in the readme and specifically the _Setup env w/ `oms-bridge`_ instructions in the `chronicle-ui` repository
   2. Run `npm install` and `npm start`
   3. Navigate to the chronicle page at http://localhost:5173/
      1. If you have issues getting the page to load, ensure you have downloaded all certificates from `chronicle-ui/etc/test-certs` and marked them as 'trusted'. To do this:
         1. Open the 'Keychain Access' app on your Macbook (`CMD+Space --> 'Keychain Access'`)
         2. Click 'login' on the left sidebar
         3. The downloaded certificates from the Chronicle repo should be listed
         4. For each cert, double click the name, click the arrow next to 'Trust', and select 'Always Trust' from the first dropdown next to 'When using this certificate'
         5. If you are still having issues, try closing/reopening Chrome and/or restarting your Macbook
4. In `oms-bridge`
    1. Follow the  `oms-bridge` _Setup_ and _Running Docker Only Environment_ steps. Choose the branch/tag for the
       version of OMS you are working with. This can be found in the `oms-bridge` repository.
    2. Create a `.env` and include the following
        ```
        COMPOSE_PROFILES=remote
        OMSB_CORS_ALLOWED_ORIGIN=http://localhost:5173
        OMSB_TAG=INC-20
        DOCKER_REGISTRY=<insert_docker_registry>
        ```
    3. For RMQ Listening Sensemakers:
        1. Updates to `docker-compose.yml`
            * Comment out the `wfs-service` service so that service doesn't take items from the queue.
    4. Run `make refresh`. This may take a few minutes.
      * You can follow the `graphql` logs with `make dockerlogs c=graphql`
          * Look for "OMS Bridge Started!"
      * When restarting `oms-bridge` the next time, you use `make dockerrefresh`
5. Trigger Sensemaker execution
    1. For RMQ Listening Sensemakers (Geo, Inference, Resolution, Mil Symbol):
        1. In `oms-data-gen` (Needed for Geospatial Sensemaker Data):
            1. Follow the setup steps in the `oms-data-gen` readme.
                1. Update the `.env` to set the `OMSB_URL` and `PKCS12_PASSWORD`
                    * `OMSB_URL="https://localhost:8443/graphql"`
                    * Ask a teammate for the `PKCS12_PASSWORD` (it's the same as the value in `atoms-sensemaking`)
        2. Run the `adsb` script to start sending geo data to omsb. Example scripts
            * `poetry run python -m oms_data_gen.adsb load -j -n 150 -s 30 -o 18 -t 1 -i N11QN` (Known Loiter and node with proper attributes for Mil Symbol)
            * `poetry run python -m oms_data_gen.adsb load -j -n 150 -s 45 -t 3 -i N24211 -i N965NN -i N8318F` (Known Cotravel and Lag-Lead and node with proper attributes for Mil Symbol)
        3. Observe Geo Points being captured by the sensemakers in the atoms-sensemaking container. Upon completion,
           objects will be created in `OMS Bridge` and should be visible in `Chronicle`.
