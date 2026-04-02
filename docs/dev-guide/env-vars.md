# Environment Settings

> ***NOTE***: The *Docker Compose* column indicates if setting the variable in
> `.env` will carry over to one or more of the containers defined in
> `docker-compose.yml`. The variables that do not carry over either rely on a
> sensible default value or are configured directly in `docker-compose.yml`.


##### Service Variables

| Variable Name          | Example                                                 | Description                                                    | Docker Compose |
|:-----------------------|:--------------------------------------------------------|:---------------------------------------------------------------|:--------------:|
| `APP_LOG_LEVEL`        | `DEBUG`                                                 | Option to set log level                                        |      Yes       |
| `RELOAD_APP`           | `1`                                                     | Option to watch for changes and reload service (i.e. dev mode) |      Yes       |
| `ROOT_PATH`            | `/services/sensemaking/1.0`                             | BaseUrl for serving the project at                             |       No       |
| `UVICORN_ROOT_PATH`    | `/services/sensemaking/1.0`                             | Uvicorn baseUrl for serving the project                        |      Yes       |
| `UVICORN_SSL_KEYFILE`  | `/opt/common/pki/server.private`                        | Uvicorn baseUrl for serving the project                        |      Yes       |
| `UVICORN_SSL_KEYFILE`  | `/opt/common/pki/server.private`                        | Uvicorn baseUrl for serving the project                        |      Yes       |


##### Database Settings

> ***NOTE***: There are two database users that need to be configured (i.e.
> admin user and a regular user). There are also three different tools being
> configured by docker: the *oms_sensemaking* service, the psql command line
> tool, and [pgAdmin].


| Variable Name                 | Example                                                     | Description                                                                               | Docker Compose |
|:------------------------------|:------------------------------------------------------------|:------------------------------------------------------------------------------------------|:--------------:|
| `DB_HOST`                     | `postgis`                                                   | The database hostname                                                                     |       No       |
| `DB_PORT`                     | `5432`                                                      | Database port                                                                             |       No       |
| `DB_USER`                     | `appuser`                                                   | The regular (i.e. non-admin) username.                                                    |      Yes       |
| `DB_PASSWORD`                 | `xxxxxx`                                                    | The password for the regular db user.                                                     |      Yes       |
| `DB_SCHEMA`                   | `oms_sensemaking`                                           | Database schema name.                                                                     |       No       |
| `DB_URI`                      | `postgresql://user:password@localhost:5432/oms_sensemaking` | Database connection URI. This is an alternative to configuring the independent components |       No       |
| `DB_SSL`                      | `True`                                                      | Flag to require SSL verse just preferring SSL                                             |       No       |
| `PGADMIN_DEFAULT_EMAIL`       | `dev@blackcape.io`                                          | [pgAdmin] The login for the default pgAdmin user.                                         |      Yes       |
| `PGADMIN_DEFAULT_PASSWORD`    | `xxxxxx`                                                    | [pgAdmin] The password for the default pgAdmin user.                                      |      Yes       |
| `PGADMIN_CONFIG_LOGIN_BANNER` | `'<h4>Development Database</h4>'`                           | [pgAdmin] A login banner for pgAdmin                                                      |      Yes       |
| `DB_NAME`                     | `oms_sensemaking`                                           | The name for the oms_sensemaking database.                                                |      Yes       |
| `DB_NAME_OMSB`                | `omsb_db`                                                   | The name for the omsb_db database.                                                        |      Yes       |
| `DB_TEMPLATE`                 | `template_postgis`                                          | The template used in the creation of the application database.                            |      Yes       |
| `DB_POOL_SIZE`                | `10`                                                        | SQLAlchemy connection pool size.                                                          |       No       |
| `DB_MAX_OVERFLOW`             | `20`                                                        | SQLAlchemy max overflow connections beyond the pool size.                                 |       No       |
| `DB_POOL_TIMEOUT_SECONDS`     | `30`                                                        | Seconds to wait for a connection from the pool.                                           |       No       |


##### OMSB Settings

| Variable Name              | Example                                            | Description                                                            | Docker Compose |
|:---------------------------|:---------------------------------------------------|:-----------------------------------------------------------------------|:--------------:|
| `OMSB_VERSION`             | `3.1.7`                                            | The version of Atoms Core                                              |      Yes       |
| `OMSB_URL`                 | `https://localhost:8020/graphql`                   | URL for OMSB                                                           |       No       |
| `USER_DN`                  | `cn=test10,ou=jade,ou=meme,o=bia,st=maryland,c=us` | User DN                                                                |       No       |
| `CERT_PATH`                | `./pki/test10.pem`                                 | Path to User PEM                                                       |       No       |
| `KEY_PATH`                 | `./pki/test10.key`                                 | Path to User Key                                                       |       No       |
| `ATOMS_CACERT_PATH`        | `./etc/cacert.pem`                                 | Path to CA Cert PEM                                                    |       No       |
| `ATOMS_CLIENT_VERIFY_SSL`  | `True`                                             | Whether the service will verify ssl connections to the ATOMS API       |       No       |
| `PKCS12_PATH`              | `./etc/sensemaking_cert.pfx`                       | Path to PKCS12 Cert                                                    |       No       |
| `PKCS12_PASSWORD`          | `P@55w0rd`                                         | Password for PKCS12 Cert                                               |       No       |


#### AAC Settings
| Variable Name            | Example                                            | Description                                       | Docker Compose |
|:-------------------------|:---------------------------------------------------|:--------------------------------------------------|:--------------:|
| `DEFAULT_AAC_PORT`       | `5780`                                             | The default connection port for the AAC client    |       No       |
| `CERT_PATH`              | `./pki/test10.pem`                                 | Path to User PEM                                  |       No       |
| `KEY_PATH`               | `./pki/test10.key`                                 | Path to User Key                                  |       No       |
| `AAC_CACERT_PATH`        | `./etc/cacert.pem`                                 | Path to CA Cert PEM                               |       No       |
| `AAC_VERIFICATION_MODE`  | `True`                                             | Verify CA bundle of AAC                           |       No       |
| `AAC_CACHE_ENABLED`      | `True`                                             | Cache AAC Requests                                |       No       |
| `AAC_URL`                | `http://aac2:3000`                                 | URL for AAC                                       |       No       |


#### OMS-SDK Settings
| Variable Name             | Example | Description                           | Docker Compose |
|:--------------------------|:--------|:--------------------------------------|:--------------:|
| `CREATE_SOURCE_IF_NONE`   | `False` | Allow creation of source              |       No       |
| `CREATE_PROVIDER_IF_NONE` | `False` | Allow creation of provider            |       No       |
| `PROFILE_TRANSPORT`       | `True`  | Allow for profiling of http transport |       No       |


##### Sensemaker Settings

| Variable Name                                              | Example                                                                       | Description                                                                              | Docker Compose |
|:-----------------------------------------------------------|:------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------|:--------------:|
| `DEFAULT_ATOMS_PORT`                                       | `5346`                                                                        | The default connection port for the Atoms client                                         |       No       |
| `SRID`                                                     | `4326`                                                                        | Spatial Reference Identifier for storing Points                                          |       No       |
| `VALID_OBSERVED_THRESHOLD_SECONDS`                         | `900`                                                                         | Threshold for amount of between Track Point Observations                                 |       No       |
| `GEO_BUFFER_EXPIRE_SEC`                                   | `30 `                                                                         | How long to wait for new points before creating a new Track                              |       No       |
| `GEOHASH_LOW`                                              | `5`                                                                           | Low geohash                                                                              |       No       |
| `GEOHASH_HIGH`                                             | `7`                                                                           | High geohash                                                                             |       No       |
| `POLL_PERIOD_SECONDS`                                      | `10`                                                                          | How often to poll for new incoming Attributes                                            |       No       |
| `OPERATED_BY_IRI`                                          | `http://schema.dia.mil/DefenseIntelligenceCoreOntology/operatedBy`            | IRI for Operated By                                                                      |       No       |
| `APPLY_COMMON_SENSE_FILTERS`                               | `TRUE`                                                                        | Toggle on/off Common Sense Filtering                                                     |       No       |
| `TRACK_WEAVER_ALGORITHM`                                   | `naive`                                                                       | The track weaver algorith to use                                                         |       No       |
| `TIME_BIN_SIZE_SECONDS`                                    | `60`                                                                          | Length of time bins in seconds for grouping points in track weaver                       |       No       |
| `COMMON_SENSE_FILTER_RULES_FILE_PATH`                      | `./data/common_sense_filter_rules.json`                                       | Path to the Common Sense Filter Rules config file                                        |       No       |
| `CONFIDENCE_WEIGHT_UNKNOWN`                                | `0.5`                                                                         | Weight to give points with UNKNOWN observation confidence                                |       No       |
| `CONFIDENCE_WEIGHT_HIGH`                                   | `1.0`                                                                         | Weight to give points with HIGH observation confidence                                   |       No       |
| `CONFIDENCE_WEIGHT_MODERATE`                               | `0.5`                                                                         | Weight to give points with MODERATE observation confidence                               |       No       |
| `CONFIDENCE_WEIGHT_LOW`                                    | `0.1`                                                                         | Weight to give points with LOW observation confidence                                    |       No       |
| `DETECT_LOITERS`                                           | `True`                                                                        | Toggle on/off Loiter Detection                                                           |       No       |
| `LAG_LEAD_ACTIVITY_NAME`                                   | `LagLead`                                                                     | Name prefix for OMSB LagLead Event Nodes                                                 |       No       |
| `LOITER_ACTIVITY_NAME`                                     | `Loiter`                                                                      | Name for OMSB Loiter Activity                                                            |       No       |
| `LOITER_ACTIVITY_IRI`                                      | `http://www.ontologyrepository.com/CommonCoreOntologies/IntentionalAct`       | OMSB Loiter Activity class IRI                                                           |       No       |
| `LOITER_ACTIVITY_STATE`                                    | `LOITER`                                                                      | OMSB Loiter Activity state                                                               |       No       |
| `LOITER_MIN_TIME`                                          | `900`                                                                         | Minimum amount of time for a valid Loiter Event                                          |       No       |
| `LOITER_GEOHASH`                                           | `5`                                                                           | Geohash for Loiter                                                                       |       No       |
| `COTRAVEL_ACTIVITY_NAME`                                   | `Cotravel`                                                                    | Name prefix for OMSB Cotravel Event Nodes                                                |       No       |
| `COTRAVEL_ACTIVITY_STATE`                                  | `COTRAVEL`                                                                    | The activity state which describes a cotravel activity                                   |       No       |
| `COTRAVEL_GEOHASH`                                         | `5`                                                                           | Geohash for Cotravel                                                                     |       No       |
| `COTRAVEL_IRI`                                             | `http://www.ontologyrepository.com/CommonCoreOntologies/IntentionalAct`       | OMSB Cotravel Event Node IRI                                                             |       No       |
| `COTRAVEL_RELATIONSHIP_IRI`                                | `http://purl.obolibrary.org/obo/BFO_0000197`                                  | OMSB Cotravel Event Node to Track Relationship IRI                                       |       No       |
| `COTRAVEL_RELATION_NAME`                                   | `inheres in`                                                                  | OMSB Cotravel Event Node to Track Relationship Name                                      |       No       |
| `SIMILAR_TRACKS_GEOHASH`                                   | `5`                                                                           | Geohash for Similar Tracks                                                               |       No       |
| `DETECT_COTRAVELS`                                         | `True`                                                                        | Toggle on/off Cotravel Detection                                                         |       No       |
| `MIN_COTRAVEL_DURATION_SECONDS`                            | `1200`                                                                        | Minimum between Objects in a Track for a Cotravel Event                                  |       No       |
| `MIN_LAG_LEAD_DURATION_SECONDS`                            | `1200`                                                                        | Minimum amount between Objects in a Track for a Lag/Lead Event                           |       No       |
| `MAX_LAG_LEAD_DURATION_SECONDS`                            | `2700`                                                                        | Maximum between Objects in a Track for a Lag/Lead Event                                  |       No       |
| `MAX_POTENTIAL_DUPLICATE_TIME_DIFF_SECONDS`                | `30`                                                                          | Max amount of time between colocated points to qualify a potential duplicate             |       No       |
| `POTENTIAL_DUPLICATE_RELATIONSHIP_NAME`                    | `Potential Duplicate`                                                         | Name for OMSB Potential Duplicate                                                        |       No       |
| `SIMILAR_TRACKS`                                           | `True`                                                                        | Toggle on/off Similar Track Calculations                                                 |       No       |
| `N_TRACKS`                                                 | `5`                                                                           | Number of similar tracks to return                                                       |       No       |
| `WITHIN_METERS`                                            | `3000.0`                                                                      | Used to define the search space for potential similar tracks                             |       No       |
| `GENERATE_INFERENCES`                                      | `True`                                                                        | Turn the Inference Sensemaker On/Off                                                     |      Yes       |
| `TOGGLE_ADD_GARRISON_RULE`                                 | `True`                                                                        | Turn the Garrison Rule On/Off                                                            |      Yes       |
| `TOGGLE_INCURSION_RULE`                                    | `True`                                                                        | Turn the Incursion Rule On/Off                                                           |      Yes       |
| `TOGGLE_TEST_ENDPOINT`                                     | `False`                                                                       | Toggle on/off test endpoints                                                             |       No       |
| `INFERENCE_TAGS`                                           | `'["Atoms Sensemaking", "Inferred Data"]'`                                    | Tags Inference Sensemaker adds to data                                                   |       No       |
| `INCURSION_TAGS`                                           | `'["Atoms Sensemaking", "Inferred Data", "Incursion"]'`                       | Incursion Tags                                                                           |       No       |
| `INCURSION__ATTRIBUTE_IRI`                                 | `https://blackcape.io/PLACEHOLDER/Incursion`                                  | Iri to apply for the Incursion Attribute                                                 |       No       |
| `INCURSION__CLASS_IRI`                                     | `http://www.ontologyrepository.com/CommonCoreOntologies/IntentionalAct`       | Iri to apply for the Incursion Activity class                                            |       No       |
| `INCURSION__ACTIVITY_STATE`                                | `UNKNOWN`                                                                     | Incursion Activity State                                                                 |       No       |
| `INCURSION__AREAS_OF_INTEREST_PATH`                        | `./data/areas_of_interest.json`                                               | Path to areas_of_interest.json file in atoms-sensemaking                                 |       No       |
| `GEO_ATTRIBUTE_IRI`                                        | `https://foundry.ai.mil/ontology/4901-001/hasCoordinates`                     | Iri for geo attribute                                                                    |       No       |
| `GEO_SENSEMAKER_CONFIG_FILE_PATH`                          | `data/geo_sensemaker_config.json`                                             | Path to the Geospatial Sensemaker Config                                                 |       No       |
| `GEO_SENSEMAKER_EVENT_TAG`                                 | `geosensemaker`                                                               | Tag for OMSB objects from the geospatial sensemakers                                     |       No       |
| `GEO_SENSEMAKER_CONFIG_DEFAULT_PROVIDER_ID`                | `00000000-0000-0000-0000-000000000000`                                        | Default provider ID in geo sensemaker config file                                        |       No       |
| `TRACK_IRI`                                                | `https://foundry.ai.mil/ontology/4901-001/ObjectTrack`                        | IRI for Tracks attribute                                                                 |       No       |
| `OBSERVABLES`                                              | `True`                                                                        | Toggle on/off Observable updates                                                         |       No       |
| `OUT_OF_GARRISON_SETTINGS__GARRISONED_IN_RELATIONSHIP_IRI` | `https://foundry.ai.mil/ontology/4901-001/garrisonedIn`                       | Iri for relationship between an object and its garrison                                  |       No       |
| `OUT_OF_GARRISON_SETTINGS__GARRISON_CLASS_IRI`             | `http://www.ontologyrepository.com/CommonCoreOntologies/IntentionalAct`       | Iri for garrison activity class                                                          |       No       |
| `OUT_OF_GARRISON_SETTINGS__IN_GARRISON_ACTIVITY_NAME`      | `In Garrison`                                                                 | Name for In Garrison activities                                                          |       No       |
| `OUT_OF_GARRISON_SETTINGS__OUT_OF_GARRISON_ACTIVITY_NAME`  | `Out of Garrison`                                                             | Name for Out of Garrison activities                                                      |       No       |
| `OUT_OF_GARRISON_SETTINGS__IN_GARRISON_ACTIVITY_STATE`     | `IN_GARRISON`                                                                 | In Garrison Activity State                                                               |       No       |
| `OUT_OF_GARRISON_SETTINGS__OUT_OF_GARRISON_ACTIVITY_STATE` | `OUT_OF_GARRISON`                                                             | Out of Garrison Activity State                                                           |       No       |
| `OUT_OF_GARRISON_SETTINGS__GARRISON_DISTANCE_KILOMETERS`   | `2000`                                                                        | Distance to use for the Out of Garrison Rule                                             |       No       |
| `ENABLE_RESOLUTION_SENSEMAKER`                             | `True`                                                                        | Toggle on/off Entity Resolution                                                          |       No       |
| `RESOLUTION_SENSEMAKER_TAG`                                | `resolution`                                                                  | Tag for OMSB objects from the resolution sensemaker                                      |       No       |
| `RESOLUTION_RELATIONSHIP_NAME`                             | `Same As`                                                                     | Relationship name for resolution sensemaker suggestions                                  |       No       |
| `RESOLUTION_RELATIONSHIP_IRI`                              | `https://foundry.ai.mil/MIDB/V3.3/relates_to`                                 | Iri to set for the Resolution Finding URL                                                |       No       |
| `DUPLICATE_OBJECT_IRIS_FILE_PATH`                          | `./data/duplicate_object_iris.json`                                           | Path to file containing duplicate object iris dictionary                                 |       No       |
| `MAX_TRACK_TIME_LENGTH_SECONDS`                            | `86400`                                                                       | Max amount of time in seconds a track can be from earliest start time to last start time |       No       |
| `MIL_SYMBOL_SETTINGS__ENABLE_MIL_SYMBOL_SENSEMAKER`        | `True`                                                                        | Toggle on/off Entity Resolution                                                          |       No       |
| `MIL_SYMBOL_SETTINGS__AFFILIATION_IRIS`                    | `'["https://foundry.ai.mil/MIDB_GST/v1/Affiliation"]'`                        | List of Affiliation IRIs to enrich from                                                  |       No       |
| `MIL_SYMBOL_SETTINGS__STATUS_IRIS`                         | `'["https://foundry.ai.mil/DICO/v3.1.0/Condition"]'`                          | List of Status IRIs to enrich from                                                       |       No       |
| `MIL_SYMBOL_SETTINGS__RULES_FILE_PATH`                     | `./data/mil_symbol_rules.json`                                                | Path to the Mil Symbol Rules config file                                                 |       No       |
| `MIL_SYMBOL_SETTINGS__ATTRIBUTE_CODE_IRIS`                 | `'["http://www.ontologyrepository.com/CommonCoreOntologies/has_text_value"]'` | Attribute Iris for full mil symbol codes                                                 |       No       |
| `MIL_SYMBOL_SETTINGS__ECHELON_IRIS`                        | `'["https://oms.dodiis.ic.gov/ontology/p-0000000029"]'`                       | Echelon IRI                                                                              |       No       |
| `MIL_SYMBOL_SETTINGS__B_C_PLACEHOLDERS`                    | `'["-", "*"]'`                                                                | Possible placeholder values for 2525B and 2525C codes                                    |       No       |
| `MAXIMUM_OMS_API_CALLS`                                    | `500`                                                                         | Maximum amount of calls allowed to be made to ATOMS within a given time period           |       No       |
| `OMS_API_CALL_PERIOD_SECONDS`                              | `120`                                                                         | Alloted amount of time for maximum ATOMS API calls to be made                            |       No       |
| `RETHROW_ERRORS_ENABLED`                                   | `True`                                                                        | Enable rethrowing of sensemaking errors                                                  |       No       |
| `TTL_CACHE_SIZE`                                           | `1024`                                                                        | Max items in a given TTL Cache                                                           |       No       |
| `TTL_CACHE_SECONDS`                                        | `3600`                                                                        | Max time to live in a given TTL Cache                                                    |       No       |
| `OMS_CRUD_TTL_CACHE_SIZE`                                  | `1024`                                                                        | Max items in ATOMS CRUD Tool's given TTL Cache                                           |       No       |
| `OMS_CRUD_TTL_CACHE_SECONDS`                               | `3600`                                                                        | Max time to live in ATOMS CRUD Tool's given TTL Cache                                    |       No       |
| `MIL_SYMBOL_SETTINGS__ECHELON_IRIS`                        | `'["https://oms.dodiis.ic.gov/ontology/p-0000000029"]'`                       | Echelon IRI                                                                              |       No       |
| `MIL_SYMBOL_SETTINGS__B_C_PLACEHOLDERS`                    | `'["-", "*"]'`                                                                | Possible placeholder values for 2525B and 2525C codes                                    |       No       |
| `AAC_CACHE_ENABLED`                                        | `True`                                                                        | Boolean to enable Local AAC Caching                                                      |       No       |
| `AAC_CACHE_STORAGE_TTL_SECONDS`                            | `300`                                                                         | How long for responses to persist in Local AAC Cache before expiring                     |       No       |
| `SM_TEST_TAGS`                                             | `["SM_TEST"]                                                                  | Tag to apply to data created during tests                                                |       No       |
| `ENABLE_AUDIT_LOG_ERROR_LOGGING`                           | `True`                                                                        | Enable audit log error logging                                                           |       No       |
| `AUDIT_LOG_ERROR_MAX_TB_CHARS`                             | `200`                                                                         | Number of characters allowed in the audit log traceback                                  |       No       |
| `AUDIT_LOG_ERROR_JSON_FILE_PATH`                           | `./data/audit_log_error.json`                                                 | Classification to set as default for Audit Log Errors                                    |       No       |
| `USER_DN_WHITELIST_PATH`                                   | `./data/whitelist.txt`                                                        | File path to the user whitelist for privileged requests                                  |       No       |
| `OBJECT_STANDARDS_SETTINGS__BUFFER_EXPIRE_SEC`             | `30`                                            | Delay in seconds to wait before processing Atoms Objects for Object Standards checks                       | No             |

#### Sensemaker Labels
| Variable Name         | Example                | Description                               | Docker Compose |
|:----------------------|:-----------------------|:------------------------------------------|:--------------:|
| `SM_CONNECTED_TRACK`  | `SM_CONNECTED_TRACK`   | Label for tracks generated by sensemaking |       No       |
| `SM_ENRICHED_LABEL`   | `SM_ENRICHED`          | Label for enriched sensemaking data       |       No       |
| `SM_INFERENCED_LABEL` | `SM_INFERENCED`        | Label for all sensemaking generated data  |       No       |
| `GEOSPATIAL_SM_LABEL` | `GEOSPATIAL_SM`        | Label for geospatial sensemaking data     |       No       |
| `COTRAVEL_SM_LABEL`   | `COTRAVEL_SM`          | Label for cotravel sensemaker             |       No       |
| `LOITER_SM_LABEL`     | `LOITER_SM`            | Label for loiter sensemaker data          |       No       |
| `INFERENCE_SM_LABEL`  | `INFERENCE_SM`         | Label for inference sensemaking data      |       No       |
| `INCURSION_SM_LABEL`  | `INCURSION_RULE`       | Label for incursion sensemaking data      |       No       |
| `GARRISON_SM_LABEL`   | `IN/OUT_GARRISON_RULE` | Label for garrison sensemaking data       |       No       |
| `MIL_SYM_SM_LABEL`    | `MILITARY_SYMBOL_SM`   | Label for mil sym sensemaking data        |       No       |
| `RES_SM_LABEL`        | `RESOLUTION_SM`        | Label for resolution sensemaking data     |       No       |


#### RabbitMQ Settings

| Variable Name              | Example                    | Description                                                     | Docker Compose |
|:---------------------------|:---------------------------|:----------------------------------------------------------------|:--------------:|
| `QUEUE_WORKER_THREADS`     | `10`                       | The amount of worker threads for a given queue's sync processes |       No       |
| `RABBITMQ_HOST`            | `rabbitmq`                 | RabbitMQ host                                                   |       No       |
| `RABBITMQ_PORT`            | `/`                        | RabbitMQ port                                                   |       No       |
| `RABBITMQ_VHOST`           | `rabbitmq`                 | RabbitMQ virtual host                                           |       No       |
| `RABBITMQ_USERNAME`        | `some_user`                | RabbitMQ username                                               |       No       |
| `RABBITMQ_PASSWORD`        | `XXXXXXXXX`                | RabbitMQ password                                               |       No       |
| `RABBITMQ_PREFETCH_COUNT`  | `200`                      | RabbitMQ prefetch count                                         |       No       |
| `RMQ_READ_WAIT_SECONDS`    | `5`                        | How long to wait when waiting for RMQ messages                  |       No       |
| `RMQ_GEO_QUEUE_NAME`       | `geo-sensemaker-trigger`   | The RMQ Geo Sensemaker Queue name                               |       No       |
| `RMQ_INFERENCE_QUEUE_NAME` | `infer-sensemaker-trigger` | The RMQ Inference Sensemaker Queue name                         |       No       |
| `RMQ_RES_QUEUE_NAME`       | `infer-sensemaker-trigger` | The RMQ Resolution Queue name                                   |       No       |


##### Connectivity Ping Settings

| Variable Name                 | Example | Description                                          | Docker Compose |
|:------------------------------|:--------|:-----------------------------------------------------|:--------------:|
| `PING_TIMEOUT_SECONDS`        | `3.0`   | Timeout in seconds for service ping checks           |       No       |
| `PING_WAIT_RETRIES`           | `5.0`   | Number of retries when waiting for service readiness |       No       |
| `PING_WAIT_DELAY_SECONDS`     | `2.0`   | Delay between readiness retries in seconds           |       No       |

##### OpenTelemetry Settings

| Variable Name                 | Example             | Description                                  | Docker Compose |
|:------------------------------|:--------------------|:---------------------------------------------|:--------------:|
| `ENABLE_TELEMETRY`            | `True`              | Enable OpenTelemetry metrics collection      |       No       |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://tempo:4317` | Distance to use for the Out of Garrison Rule |       No       |
| `OTEL_SERVICE_NAME`           | `atoms-sensemaking` | OpenTelemetry service name                   |       No       |
| `OTEL_TRACES_SAMPLER`         | `always_on`         | OpenTelemetry traces sampler                 |       No       |


##### UI/Display Settings

| Variable Name                    | Example                           | Description                                                    | Docker Compose |
|:---------------------------------|:----------------------------------|:---------------------------------------------------------------|:--------------:|
| `CLASSIFICATION_BANNER_TEXT`     | `UNCLASSIFIED`                    | Text to display in the classification banner                   |       No       |
| `CLASSIFICATION_BANNER_COLOR`    | `#00c853`                         | Background color for the classification banner                 |       No       |
