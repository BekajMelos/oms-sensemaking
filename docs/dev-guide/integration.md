# Integrating Sensemaking with other OMS services

### Steps to see Sensemaker objects with Chronicle

1. Repos needed: `chronicle-ui`, `oms-bridge`, `oms-data-gen` (for Geospatial), `oms-sensemaking`
2. In `oms-sensemaking`
    1. Deteremine your IP address: `ipconfig getifaddr en0`
    2. Update the `.env` with the following values. _Please note the uncommented and commented settings_
        * `# POSTGRES_PORT=5432`
        * `# CORENLP_EXPOSE_PORT=9000`
        * `# CORENLP_HOST=corenlp:9000`
        * `RMQ_GEO_QUEUE_NAME=oms-wfs-trigger`
        * `OMSB_VERSION=<OMSB_VERSION>`
        * `OMSB_URL="https://<your_ip_address>:8443/graphql"`
        * `AAC_URL="http://<your_ip_address>:5022"`
    3. Set the sensemaker sqs queue url. `oms-bridge` does not support all of our SQS Queues, so only one sensemaker can be used at a time at the moment.
        1. Update the `.env` to set the SQS queue to the wfsTrigger (we're temporarily using that queue)
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
        DOCKER_REGISTRY=tex.gerbil-cloud.ts.net:5000
        ```
    3. For SQS Listening Sensemakers:
        1. Updates to `docker-compose.yml`
            * Comment out the `wfs-service` service so that service doesn't take items from the queue.
    4. Run `make refresh`. This may take a few minutes.
      * You can follow the `graphql` logs with `make dockerlogs c=graphql`
          * Look for "OMS Bridge Started!"
      * You can follow the `localstack` logs with `make dockerlogs c=localstack`
          * Look for "Ready."
      * When restarting `oms-bridge` the next time, you use `make dockerrefresh`
5. Trigger Sensemaker execution
    1. For NLP Sensemakers:
       1. Now you should be able to run the Sensemaking API endpoints and view the results published to OMS in Chronicle
            1. Make sure to create an Originator, Provider, and Source in Chronicle so that you can copy a valid source ID for the NLP API call. To do this:
                1. Click the 'Data Types' icon in the left sidebar
                2. Select 'Sourcing'
                3. On the Sourcing page, ensure you are on the 'Sources' tab and click 'Actions' and 'Add Source'
                4. Work through the creation steps. In creating a Source, you will also be prompted to create a Provider and Originator.
            2. If the CoreNLP container quits unexpectedly with no error message upon API call, allocate more resources to docker and try again
            3. Check out the Objects, Relationships, and Attributes! The Nodes/Relationships you see in Chronicle should resemble those in the response of the FastAPI call. (See below example)

        - Below is a sample request with the `source_id` and `text` fields filled out. You must change the `source_id` for it to work, but feel free to use this text sample, which is an excerpt from `etc/data/russia-ukraine.txt`:

        ```
        {
        "source_id": "2d2a5a4d-b43d-4763-af9e-6369285985be",
        "acm": {
            "accms": [],
            "atom_energy": [],
            "banner": "UNCLASSIFIED",
            "classif": "U",
            "disp_only": "",
            "disponly_to": [
            ""
            ],
            "dissem_countries": [
            "USA"
            ],
            "dissem_ctrls": [],
            "f_accms": [],
            "f_atom_energy": [],
            "f_clearance": [
            "u"
            ],
            "f_macs": [],
            "f_missions": [],
            "f_oc_org": [],
            "f_regions": [],
            "f_sar_id": [],
            "f_sci_ctrls": [],
            "f_share": [],
            "fgi_open": [],
            "fgi_protect": [],
            "macs": [],
            "non_ic": [],
            "oc_attribs": [
            {
                "missions": [],
                "orgs": [],
                "regions": []
            }
            ],
            "owner_prod": [
            "USA"
            ],
            "portion": "U",
            "rel_to": [],
            "sar_id": [],
            "sci_ctrls": [],
            "version": "2.1.0"
        },
        "text": "As Ukraine Invades Russia, Kyiv's Troops Are in Trouble on the Eastern Front Ukrainian soldiers are overmatched in some areas and deployments in the trenches can stretch for months  NEAR KRASNOHORIVKA, Ukraine—As Ukrainian troops poured into Russia's Kursk region last week, five Russian assault troops on motorbikes were zipping toward Ukraine's front line hundreds of miles to the east.  Two of the bikers were gunned down. Another turned back and fled. But the last two escaped into the trees, looking for a place to hunker down and await reinforcements.  This is one of the tactics Russia is using to take advantage of its vastly larger number of troops in the Donetsk region of eastern Ukraine, Russia's primary target and the site of intensified assaults this week despite Ukraine's incursion into Russia. Ukraine's threadbare troops are struggling to hold them back.  The 21st Battalion of Ukraine's Separate Presidential Brigade is fighting to keep Russian forces at bay, including with mortar fire near the town of Krasnohorivka.  Ukraine's Kursk operation has embarrassed President Vladimir Putin and given Kyiv the tactical initiative in one area for the first time in nearly a year. But it transferred troops and weapons from its already-creaking front lines to pull it off, a gamble that risks making a bad situation worse.  'We don't have enough people to do our job properly,' said the commander of the 21st Battalion of the Separate Presidential Brigade, which faced the Russian assault last week at the edge of the contested town of Krasnohorivka.  Russian forces have gained territory at a faster rate this summer than at any point since the first weeks of the war and are now pushing toward the logistical hub of Pokrovsk."
        }
        ```

        - The following Entity in the API Response would show up in Chronicle with `Name: Ukraine`, and `Class: Geographical Location` or `Entity`

        ```
            {
                "type": "Location",
                "objectId": "EntityMention-71",
                "uuid": "77d3ee8e-f906-4572-8f80-958486dc92f7",
                "hstart": "1",
                "hend": "2",
                "estart": "1",
                "eend": "2",
                "headPosition": "1",
                "value": "Ukraine",
                "corefID": "-1"
            },
        ```

        - The following Relationship in the API Response would show up in Chronicle with `Start Object: Kyiv`, `Relationship: located in at some time`, `End Object: Ukraine`

        ```
        {
                "type": "Located_In",
                "objectId": "RelationMention-13",
                "uuid": "c8ce0562-43e9-4cfb-b8c9-e7eb6c2c61aa",
                "start": "1",
                "end": "6",
                "relations": [
                "Located_In, 0.4126628720267475",
                "Has_Job, 0.21216090765746073",
                "Part_of_Org, 0.1998946200003775",
                "_NR, 0.17528160031541418"
                ],
                "entities": [
                {
                    "type": "Location",
                    "objectId": "EntityMention-75",
                    "uuid": "31760e4f-7bc4-473f-b2d8-76bfb8ae2c2f",
                    "hstart": "5",
                    "hend": "6",
                    "estart": "5",
                    "eend": "6",
                    "headPosition": "5",
                    "value": "Kyiv",
                    "corefID": "-1"
                },
                {
                    "type": "Location",
                    "objectId": "EntityMention-71",
                    "uuid": "77d3ee8e-f906-4572-8f80-958486dc92f7",
                    "hstart": "1",
                    "hend": "2",
                    "estart": "1",
                    "eend": "2",
                    "headPosition": "1",
                    "value": "Ukraine",
                    "corefID": "-1"
                }
                ]
            },
        ```

        - Additionally, a `Report` Object should exist and have a `Relationship: describes` to every single Entity that it produced.
    2. For SQS Listening Sensemakers (Geo, Inference, Resolution, Mil Symbol):
        1. In `oms-data-gen` (Needed for Geospatial Sensemaker Data):
            1. Follow the setup steps in the `oms-data-gen` readme.
                1. Update the `.env` to set the `OMSB_URL` and `PKCS12_PASSWORD`
                    * `OMSB_URL="https://localhost:8443/graphql"`
                    * Ask a teammate for the `PKCS12_PASSWORD` (it's the same as the value in `oms-sensemaking`)
        2. Run the `adsb` script to start sending geo data to omsb. Example scripts
            * `poetry run python -m oms_data_gen.adsb load -j -n 150 -s 30 -o 18 -t 1 -i N11QN` (Known Loiter and node with proper attributes for Mil Symbol)
            * `poetry run python -m oms_data_gen.adsb load -j -n 150 -s 45 -t 3 -i N24211 -i N965NN -i N8318F` (Known Cotravel and Lag-Lead and node with proper attributes for Mil Symbol)
        3. Observe Geo Points being captured by the sensemakers in the oms-sensemaking container. Upon completion,
           objects will be created in `OMS Bridge` and should be visible in `Chronicle`.
