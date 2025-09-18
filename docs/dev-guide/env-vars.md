# Environment Settings

> ***NOTE***: The *Docker Compose* column indicates if setting the variable in
> `.env` will carry over to one or more of the containers defined in
> `docker-compose.yml`. The variables that do not carry over either rely on a
> sensible default value or are configured directly in `docker-compose.yml`.


##### Service Variables

| Variable Name          | Example                                                 | Description                                                    | Docker Compose |
|:-----------------------|:--------------------------------------------------------|:---------------------------------------------------------------|:--------------:|
| `APP_LOG_LEVEL`        | `DEBUG`                                                 | Option to set log level                                        | Yes            |
| `RELOAD_APP`           | `1`                                                     | Option to watch for changes and reload service (i.e. dev mode) | Yes            |
| `ROOT_PATH`            | `/services/sensemaking/1.0`                             | BaseUrl for serving the project at                             | No             |
| `UVICORN_ROOT_PATH`    | `/services/sensemaking/1.0`                             | Uvicorn baseUrl for serving the project                        | Yes            |
| `UVICORN_SSL_KEYFILE`  | `/opt/common/pki/server.private`                        | Uvicorn baseUrl for serving the project                        | Yes            |
| `UVICORN_SSL_KEYFILE`  | `/opt/common/pki/server.private`                        | Uvicorn baseUrl for serving the project                        | Yes            |


##### Database Settings

> ***NOTE***: There are two database users that need to be configured (i.e.
> admin user and a regular user). There are also three different tools being
> configured by docker: the *oms_sensemaking* service, the psql command line
> tool, and [pgAdmin].


| Variable Name                 | Example                           | Description                                                                                                   | Docker Compose |
|:------------------------------|:----------------------------------|:--------------------------------------------------------------------------------------------------------------|:--------------:|
| `DB_HOST`                     | `postgis`                         | The database hostname                                                                                         | No             |
| `DB_USER`                     | `appuser`                         | The regular (i.e. non-admin) username.                                                                        | Yes            |
| `DB_PASSWORD`                 | `xxxxxx`                          | The password for the regular db user.                                                                         | Yes            |
| `POSTGRES_USER`               | `postgres`                        | The PostgreSQL/PostGIS admin user                                                                             | Yes            |
| `POSTGRES_PASSWORD`           | `xxxxxxx`                         | The password for the PostgreSQL admin user                                                                    | Yes            |
| `POSTGRES_PORT`               | `5432`                            | The port for the PostgreSQL service. When set, this will expose the port to the host (needed for unit tests). | Yes            |
| `PGADMIN_DEFAULT_EMAIL`       | `dev@blackcape.io`                | [pgAdmin] The login for the default pgAdmin user.                                                             | Yes            |
| `PGADMIN_DEFAULT_PASSWORD`    | `xxxxxx`                          | [pgAdmin]The password for the default pgAdmin user.                                                           | Yes            |
| `PGADMIN_CONFIG_LOGIN_BANNER` | `'<h4>Development Database</h4>'` | [pgAdmin]A login banner for pgAdmin                                                                           | Yes            |
| `DB_NAME`                     | `oms_sensemaking`                 | The name for the oms_sensemaking database.                                                                    | Yes            |
| `DB_NAME_OMSB`                | `omsb_db`                         | The name for the omsb_db database.                                                                            | Yes            |
| `DB_TEMPLATE`                 | `template_postgis`                | The template used in the creation of the application database.                                                | Yes            |



##### AWS Settings

| Variable Name           | Example                                             | Description                           | Docker Compose |
|:------------------------|:----------------------------------------------------|:--------------------------------------|:--------------:|
| `AWS_ENDPOINT_URL`      | `http://localhost:4566` or `http://localstack:4566` or `http://<your_ip>:4566` | AWS Endpoint                          | No             |
| `AWS_ACCESS_KEY_ID`     | `FAKE`                                              | AWS Access Key                        | No             |
| `AWS_SECRET_ACCESS_KEY` | `FAKE`                                              | AWS Secret Key                        | No             |
| `AWS_REGION_NAME`       | `us-east-1`                                         | AWS Region                            | No             |
| `AWS_USE_SSL`           | `False`                                             | Boolean to use SSL for SQS Connection | No             |
| `AWS_VERIFY`            | `False`                                             | Boolean to use SSL verifiation        | No             |


##### OMSB Settings

| Variable Name  | Example                                            | Description               | Docker Compose |
|:---------------|:---------------------------------------------------|:--------------------------|:--------------:|
| `OMSB_VERSION` | `Grimlock-INC-30`                                  | The version of oms-bridge | Yes            |
| `OMSB_URL`     | `https://localhost:8020/graphql`                   | URL for OMSB              | No             |
| `USER_DN`      | `cn=test10,ou=jade,ou=meme,o=bia,st=maryland,c=us` | User DN                   | No             |
| `CERT_PATH`    | `./pki/test10.pem`                                 | Path to User PEM          | No             |
| `KEY_PATH`     | `./pki/test10.key`                                 | Path to User Key          | No             |
| `ATOMS_CACERT_PATH`  | `./etc/cacert.pem`                                 | Path to CA Cert PEM       | No             |
| `PKCS12_PATH`  | `./etc/sensemaking_cert.pfx`                       | Path to PKCS12 Cert       | No             |
| `PKCS12_PASSWORD`| `P@55w0rd`                                       | Password for PKCS12 Cert  | No             |

#### AAC Settings
| Variable Name            | Example                                            | Description               | Docker Compose |
|:-------------------------|:---------------------------------------------------|:--------------------------|:--------------:|
| `CERT_PATH`              | `./pki/test10.pem`                                 | Path to User PEM          | No             |
| `KEY_PATH`               | `./pki/test10.key`                                 | Path to User Key          | No             |
| `AAC_CACERT_PATH`            | `./etc/cacert.pem`                                 | Path to CA Cert PEM       | No             |
| `AAC_VERIFICATION_MODE`  | `True`                                             | Verify CA bundle of AAC   | No             |
| `AAC_CACHE_ENABLED`      | `True`                                             | Cache AAC Requests        | No             |

##### Sensemaker Settings

| Variable Name                                       | Example                                                                                           | Description                                                    | Docker Compose |
|:----------------------------------------------------|:--------------------------------------------------------------------------------------------------|:---------------------------------------------------------------|:--------------:|
| `SRID`                                              | `4326`                                                                                            | Spatial Reference Identifier for storing Points                | No             |
| `VALID_OBSERVED_THRESHOLD_SECONDS`                  | `900`                                                                                             | Threshold for amount of between Track Point Observations       | No             |
| `CACHE_ENTRY_EXPIRE_SEC`                            | `30 `                                                                                             | How long to wait for new points before creating a new Track    | No             |
| `GEOHASH_LOW`                                       | `5`                                                                                               | Low geohash                                                    | No             |
| `GEOHASH_HIGH`                                      | `7`                                                                                               | High geohash                                                   | No             |
| `POLL_PERIOD_SECONDS`                               | `10`                                                                                              | How often to poll for new incoming Attributes                  | No             |
| `OPERATED_BY_IRI`                                   | `http://schema.dia.mil/DefenseIntelligenceCoreOntology/operatedBy`                                | IRI for Operated By                                            | No             |
| `APPLY_COMMON_SENSE_FILTERS`                        | `TRUE`                                                                                            | Toggle on/off Common Sense Filtering                           | No             |
| `TRACK_WEAVER_ALGORITHM`                            |`naive`                                                             | The track weaver algorith to use              | No             |
| `TIME_BIN_SIZE_SECONDS`                            |`60`                                                             | Length of time bins in seconds for grouping points in track weaver              | No             |
| `COMMON_SENSE_FILTER_RULES_FILE_PATH`               | `./data/common_sense_filter_rules.json`                                                           | Path to the Common Sense Filter Rules config file              | No             |
| `CONFIDENCE_WEIGHT_UNKNOWN`                         | `0.5`                                                                                             | Weight to give points with UNKNOWN observation confidence      | No             |
| `CONFIDENCE_WEIGHT_HIGH`                            | `1.0`                                                                                             | Weight to give points with HIGH observation confidence         | No             |
| `CONFIDENCE_WEIGHT_MODERATE`                        | `0.5`                                                                                             | Weight to give points with MODERATE observation confidence     | No             |
| `CONFIDENCE_WEIGHT_LOW`                             | `0.1`                                                                                             | Weight to give points with LOW observation confidence          | No             |
| `DETECT_LOITERS`                                    | `True`                                                                                            | Toggle on/off Loiter Detection                                 | No             |
| `LOITER_MIN_TIME`                                   | `900`                                                                                             | Minimum amount of time for a valid Loiter Event                | No             |
| `DETECT_COTRAVELS`                                  | `True`                                                                                            | Toggle on/off Cotravel Detection                               | No             |
| `MIN_COTRAVEL_DURATION_SECONDS`                     | `1200`                                                                                            | Minimum between Objects in a Track for a Cotravel Event        | No             |
| `MIN_LAG_LEAD_DURATION_SECONDS`                     | `1200`                                                                                            | Minimum amount between Objects in a Track for a Lag/Lead Event | No             |
| `MAX_LAG_LEAD_DURATION_SECONDS`                     | `2700`                                                                                            | Maximum between Objects in a Track for a Lag/Lead Event        | No             |
| `SIMILAR_TRACKS`                                    | `True`                                                                                            | Toggle on/off Similar Track Calculations                       | No             |
| `N_TRACKS`                                          | `5`                                                                                               | Number of similar tracks to return                             | No             |
| `WITHIN_METERS`                                     | `3000.0`                                                                                          | Used to define the search space for potential similar tracks   | No             |
| `SQS_GEO_QUEUE_URL`                                 | `http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/geoSensemakerTrigger`          | Geospatial SQS Queue URL                                       | Yes            |
| `GENERATE_INFERENCES`                               | `True`                                                                                            | Turn the Inference Sensemaker On/Off                           | Yes            |
| `TOGGLE_ADD_GARRISON_RULE`                          | `True`                                                                                            | Turn the Garrison Rule On/Off                                  | Yes            |
| `TOGGLE_INCURSION_RULE`                             | `True`                                                                                            | Turn the Incursion Rule On/Off                                 | Yes            |
| `INFERENCE_TAGS`                                    | `'["Oms Sensemaking", "Inferred Data"]'`                                                          | Tags Inference Sensemaker adds to data                         | No             |
| `INCURSION_TAGS`                          | `'["Oms Sensemaking", "Inferred Data", "Incursion"]'`                                             | Incursion Tags                                                 | No             |
| `INFERENCE_INCURSION_ATTRIBUTE_IRI`                 | `https://blackcape.io/PLACEHOLDER/Incursion`                                                      | Iri to apply for the Incursion Attribute                       | No             |
| `INFERENCE_INCURSION_CLASS_IRI`                     | `http://www.ontologyrepository.com/CommonCoreOntologies/IntentionalAct`                           | Iri to apply for the Incursion Activity class                  | No             |
| `INFERENCE_INCURSION_ACTIVITY_STATE`                | `UNKNOWN`                                                                                         | Incursion Activity State                                       | No             |
| `INFERENCE_INCURSION_AREAS_OF_INTEREST_PATH`        | `./data/areas_of_interest.json`                                                                   | Path to areas_of_interest.json file in oms-sensemaking         | No             |
| `INFERENCE_GEO_ATTRIBUTE_IRI`                       | `https://foundry.ai.mil/ontology/4901-001/hasCoordinates`                                         | Iri for geo attribute                                          | No             |
| `INFERENCE_GARRISONED_IN_IRI`                       | `https://foundry.ai.mil/ontology/4901-001/garrisonedIn`                                           | Iri for relationship between an object and its garrison        | No             |
| `INFERENCE_GARRISON_CLASS_IRI`                      | `http://www.ontologyrepository.com/CommonCoreOntologies/IntentionalAct`                           | Iri for garrison activity class                                | No             |
| `INFERENCE_IN_GARRISON_ACTIVITY_NAME`               | `In Garrison`                                                                                     | Name for In Garrison activities                                | No             |
| `INFERENCE_OUT_OF_GARRISON_ACTIVITY_NAME`           | `Out of Garrison`                                                                                 | Name for Out of Garrison activities                            | No             |
| `INFERENCE_IN_GARRISON_ACTIVITY_STATE`              | `IN_GARRISON`                                                                                     | In Garrison Activity State                                     | No             |
| `INFERENCE_OUT_OF_GARRISON_ACTIVITY_STATE`          | `OUT_OF_GARRISON`                                                                                 | Out of Garrison Activity State                                 | No             |
| `GARRISON_DISTANCE_KILOMETERS`                      | `2000`                                                                                            | Distance to use for the Out of Garrison Rule                   | No             |
| `SQS_RES_QUEUE_URL`                                 | `http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/resolutionTrigger`             | Resolution SQS Queue URL                                       | Yes            |
| `ENABLE_RESOLUTION_SENSEMAKER`                      | `True`                                                                                            | Toggle on/off Entity Resolution                                | No             |
| `RESOLUTION_SENSEMAKER_TAG`                         | `resolution_tag`                                                                                  | Tag for OMSB objects from the resolution sensemaker            | No             |
| `RESOLUTION_RELATIONSHIP_NAME`                      | `Same As`                                                                                         | Relationship name for resolution sensemaker suggestions        | No             |
| `RESOLUTION_RELATIONSHIP_IRI`                       | `https://foundry.ai.mil/MIDB/V3.3/relates_to`                                                     | Iri to set for the Resolution Finding URL                      | No             |
| `DUPLICATE_OBJECT_IRIS_FILE_PATH`                   | `./data/duplicate_object_iris.json`                                                               | Path to file containing duplicate object iris dictionary       | No             |
| `MIL_SYMBOL_SETTINGS__SQS_MIL_SYMBOL_QUEUE_URL`     | `http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/milSymbolTrigger`              | Mil Symbol SQS Queue URL                                       | Yes            |
| `MIL_SYMBOL_SETTINGS__ENABLE_MIL_SYMBOL_SENSEMAKER` | `True`                                                                                            | Toggle on/off Entity Resolution                                | No             |
| `MIL_SYMBOL_SETTINGS__AFFILIATION_IRIS`             | `'["https://foundry.ai.mil/MIDB_GST/v1/Affiliation"]'`                                            | List of Affiliation IRIs to enrich from                        | No             |
| `MIL_SYMBOL_SETTINGS__STATUS_IRIS`                  | `'["https://foundry.ai.mil/DICO/v3.1.0/Condition"]'`                                              | List of Status IRIs to enrich from                             | No             |
| `MIL_SYMBOL_SETTINGS__RULES_FILE_PATH`              | `./data/mil_symbol_rules.json`                                                                    | Path to the Mil Symbol Rules config file                       | No             |
| `MIL_SYMBOL_SETTINGS__ATTRIBUTE_CODE_IRIS`                    | `'["http://www.ontologyrepository.com/CommonCoreOntologies/has_text_value"]'`                     | Attribute Iris for full mil symbol codes                       | No             |
| `MIL_SYMBOL_SETTINGS__ECHELON_IRIS`                    | `'["https://oms.dodiis.ic.gov/ontology/p-0000000029"]'`                     | Echelon IRI                       | No             |
| `MIL_SYMBOL_SETTINGS__B_C_PLACEHOLDERS`       | `'["-", "*"]'`                     | Possible placeholder values for 2525B and 2525C codes                | No             |
| `MAXIMUM_OMS_API_CALLS`                    | `500`                     | Maximum amount of calls allowed to be made to OMS within a given time period                       | No             |
| `OMS_API_CALL_PERIOD_SECONDS`                    | `120`                     | Alloted amount of time for maximum OMS API calls to be made                       | No             |
| `MIL_SYMBOL_SETTINGS__ECHELON_IRIS`                    | `'["https://oms.dodiis.ic.gov/ontology/p-0000000029"]'`                     | Echelon IRI                       | No             |
| `MIL_SYMBOL_SETTINGS__B_C_PLACEHOLDERS`       | `'["-", "*"]'`                     | Possible placeholder values for 2525B and 2525C codes                | No             |
| `RABBITMQ_PREFETCH_COUNT`                    | `200`                     | RabbitMQ prefetch count                       | No             |
| `AAC_CACHE_ENABLED`       | `True`                     | Boolean to enable Local AAC Caching                | No             |
| `AAC_CACHE_STORAGE_TTL_SECONDS`       | `300`                     | How long for responses to persist in Local AAC Cache before expiring                | No             |
| `ENABLE_AUDIT_LOG_ERROR_LOGGING`                    | `True`                     | Enable audit log error logging                       | No             |
| `AUDIT_LOG_ERROR_MAX_TB_CHARS`                    | `200`                     | Number of characters allowed in the audit log traceback                       | No             |
| `AUDIT_LOG_ERROR_ACM_JSON_FILE_PATH`                    | `./data/audit_log_error.json`                     | Classification to set as default for Audit Log Errors                       | No             |
| `USER_DN_WHITELIST_PATH`                    | `./data/whitelist.txt`                     | File path to the user whitelist for privileged requests                       | No             |


##### UI/Display Settings

| Variable Name                    | Example                           | Description                                                    | Docker Compose |
|:---------------------------------|:----------------------------------|:---------------------------------------------------------------|:--------------:|
| `CLASSIFICATION_BANNER_TEXT`     | `UNCLASSIFIED`                    | Text to display in the classification banner                   | No             |
| `CLASSIFICATION_BANNER_COLOR`    | `#00c853`                         | Background color for the classification banner                 | No             |
