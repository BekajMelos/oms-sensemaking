# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

### Added
- New script to generate sample tracks for EKF tuning
- Compliant fields are recorded and are now part of the Object Standards grade output
- Violations are now recorded and have two types: MISSING and INVALID
- New script, called with `make performance`, to track performance of queues and post results to a .json file.

### Changed
- Cleanup of .env.template
- Refactor and break out larger files

### Fixed
- Although the custom garrison query was working, it was slightly configured incorrectly in how it retrieved activities. The query now heavily filters based off the current node.

## [0.26.0] - 2026-03-02

### Added
- Updates from `grimlock-support` through 0.19.8

### Changed
- Migrate to using atoms-local-dev environment.
- Updated all old references to 'Object Minimums' to the new name 'Object Standards'
- Updated ATOMS dependency to Starscream 3.1.6 and sdk to 14.0.0

## [0.19.11] - 2026-03-18

### Added

### Changed

### Fixed
- In/Out Garrison Sensemaker now does classification rollup correctly
- Fix Existing Incursions excluding their current classification when doing classification rollup
- Using all attributes to determine the acm of a resolution relationship

## [0.19.10] - 2026-03-16

### Added
- Added Lag/Lead finding type for cotravel outputs that get saved to the Sensemaking findings table
- Added indices for AuditLogErrors created_at for query performance
- AAC Client can retrieve an access control model for classification strings
- Added endpoint for deleting AuditLogErrors

### Changed

- Migrate to using atoms-local-dev environment.

### Fixed
- Addressed 'Blocking' and 'Critical' Sonarqube vulnerabilities. Minimized 'Major' vulnerabilites
- Addressed 'Critical' and 'High' Prisma vulnerabilities as best as posisble. Resolved issues that currently have existing solutions and mitigations

## [0.19.9] - 2026-03-09

### Added
- Pool status for the health check endpoint

### Fixed
- Although the custom garrison query was working, it was slightly configured incorrectly in how it retrieved activities. The query now heavily filters based off the current node.

## [0.19.8] - 2026-03-02

### Added
- Added aircraft and vessel configurations into 'duplicate_object_iris.json' for the Object Resolution Sensemaker

### Changed
- All Sensemaking inferred data is generated with an 'UNKNOWN' confidence value.

### Fixed
- Removed ignoreCase param in StringQuery
- Removed .value reference on confidence value enums
- removed unnecessary boolean variable and its corresponding conditional

## [0.25.0] - 2026-02-23

### Added
- Updates from `grimlock-support` through 0.19.7

### Changed
- Updated pytest and other dependencies to latest version
- Bump sdk to Starscream 13.1.0

### Fixed

## [0.24.0] - 2026-02-12

### Added
- Added Extended Kalman Filter to track weaver algorithms.
- Added compose files for using `atoms-local-dev`
- Apply throttle settings updates at application start-ups and runtime, via call to `PATCH /settings`.

### Changed
- Silenced noisy warnings and resolved async warning in Python tests.
- Updated dependencies and resolved compatibility warnings introduced by newer package versions.
- Object Minimum rubric applies to the most specific class now.
- Updated `aac2` container to latest
- Support two settings endpoints: `PATCH /settings` to update any settings at runtime and future start-ups, and `GET /settings` to get all settings stored for admin dashboard.

### Fixed
- Added 'get relationship' function to crud tool for event handling purposes. Relationship objects are now a type that can be handled.

## [0.23.1] - 2026-01-28

### Added
- Added the ability for the Object Minimum Sensemaker to record missing object characteristics

### Changed
- Modified the `GeoQueueFilter` function to filter out observations with an IRI that matches the Sensemaking Track IRI setting
- Along with a float score, the Object Minimum Sensemaker also outputs the ratio of completion, and a list of missing characteristics (currently just IRIs)
- Updated ATOMS dependency to Starscream 3.1.4
- Changed ActivityQuery `state` to StringQuery
- Changed old Incursion and Out of Garrison AtomsClient methods to "deprecated"
- Updated tests to use Mock Observation instances
- Cleaned up unused inference.py, base_rule.py, and unit tests that relies on those files

### Fixed
- ActivityQuery `name`'s StringQuery built with `in_`
- Fixed datetime and class-based `config` warnings when running `make test`

## [0.23.0] - 2026-01-26

### Added
- Object Minimum Sensemaker captures, retrieves, and processes relationship data
- Object Minimum Sensemaker filters on IRI
- Resolution Sensemaker now supports matching on any one of multiple criteria sets (e.g., `[BENUMBER+OSUFFX]` OR `[SK]`).
- Updates from `grimlock-support` 0.19.3

### Changed
- Updated unit test coverage to 80%

## [0.22.0] - 2026-01-20

### Changed
- Removed old NLP models from repository
- Updated settings to group Incursion settings and Out Of Garrison settings, and references to settings

## [0.21.0] - 2026-01-12

### Changed
- RabbitMQ Listener now imports a settings instance upon creation as a parameter

### Fixed
- Resolved occasional RuntimeError due to multiple threads iterating over node_track_mapping in the Geospatial controller.

## [0.20.0] - 2026-01-05

### Added
- Base structure for the Object Minimums Sensemaker
- Added base configuration file containing 'Person' and 'Military Unit' data for future Object Minimums Sensemaker

### Changed
- Updated ATOMS dependency to Starscream 3.1.1

## [0.19.7] - 2026-02-23

### Added
- Detect circular ontology class structure when getting class ancestors

### Changed
- Loiters now return activities
- Removed provider_id from database and splitting logic
- Mil Symbol Sensemaker utilizes new custom mutation to create attributes in one request instead of making individual API calls (performance improvement)

### Fixed
- Resolved index and comment discrepancies between alembic and SQLAlchemy models.

## [0.19.6] - 2026-02-16

### Added
- Resolution Sensemaker now supports matching on any one of multiple criteria sets (e.g., `[BENUMBER+OSUFFX]` OR `[SK]`).

### Changed
- The Cotravel sensemaker now outputs two activities (for each "cotravelling" node) and one relationship (between the "cotravelling" nodes)
- The Incursion Sensemaker no longer outputs/updates an attribute (only an activity).

## [0.19.5] - 2026-02-10

### Added
- The In/Out of Garrison Sensemaker now creates a finding type upon processing data
- The Incursion Sensemaker now creates a finding type upon processing data

### Changed
- Grimlock now uses SDK version 12.0.0
- Bump opentelemetry packages to resolve missing dependency
- Mil Symbol Sensemaker pulls ACM from the node as a default when no other ACM is available through enrichment

## [0.19.4] - 2026-02-03

### Added
- Add atoms_id and atoms_type to findings table in sensemaking database.
- Make atoms_id, atoms_type, and finding_type indexes to not slow performance.

### Changed
- Modified the `GeoQueueFilter` function to filter out observations with an IRI that matches the Sensemaking Track IRI setting
- Added `COTRAVEL_POTENTIAL_DUPLICATE` finding type to the `finding_type` enum

### Fixed
- Out of Garrison query uses `in_` to retrieve matching names

### Removed

## [0.19.3] - 2026-01-26

### Changed
- Renamed customer facing instances of OMS to ATOMS

### Added

## [0.19.2] - 2026-01-12

### Changed
- Integrate updated Garrison custom query from SDK, which now includes Activities. Remove calls to `get_activities()`.

### Removed
- Remove unused `GetGarrisonDataSequential` class from garrison_data_collection.py.
- Remove `has_action_already_ran()` from Incursion and Garrison workflows. Remove unnecessary queries to activities.

## [0.19.1] - 2026-01-06

### Added
- Add Labels to Mil Symbol Attributes

## [0.19.0] - 2026-01-05

### Added
- Added abstract method `get_graph_data()` in Inference's BaseRule. Placeholder methods to be implemented for each respective rule.
- Restoring code to split tracks by provider
- Added `INCURSION` activity state.
- Added new configuration toggle for http profile.
- Base structure for the Object Minimums Sensemaker
- Added base configuration file containing 'Person' and 'Military Unit' data for future Object Minimums Sensemaker
- Added Object Minimums Sensemaker processing
- Added ObjectMinimumGrade and ObjectMinimumRubric classes
- Added Alembic error logging in `prestart.sh` and exception coverage in `env.py`.

### Changed
- Updated tags to reference Atoms instead of oms
- Clean up formatting for environment variables
- Changed Inference Rules into their own Sensemakers which inherit from the base class for improved parallel processing.
- Instead of using the actual node object, use the nodeId of the object of interest for the Incursion and In/Out Garrison processes.
- Implemented an IRI validation step in `ResolutionQueueFilter` that restricts event processing to only those ATTRIBUTE objects whose IRIs match an entry in the `duplicate_object_iris.json` configuration.
- Combined update of incursion activity and attribute to a single request (mutation)
- Incursion retrieves a majority of its necessary data through a single custom SDK query

### Fixed
- Fixed bug where `TimeBinTrackWeaver` algorithm generated random `observation_id`s

### Removed
- No longer request for the node object in the Incursion and In/Out Garrison processes
- Removed unused OS packages for vulnerability reasons

## [0.18.0] - 2025-12-09

### Added
- Two endpoints to adjust throttling settings

### Changed
- Updated ATOMS dependency to Grimlock-INC-36
- Filter out track type observations for the Inference processes
- Transitioning `_fetch_garrison_coords()` function away from exceptions
- In compliance with coming SDK updates, the event_hooks parameter in the Sync/Async CRUD tools' clients were populated to record the time requests were sent
- Updated ATOMS dependency to Grimlock-INC-37

### Fixed
- RabbitMQ queues are now thread safe so they no longer lose connection

## [0.17.2] - 2025-11-19

### Removed
- Revert adding provider_id to tracks in database and splitting tracks by provider due to migration issues in deployment environments

## [0.17.1] - 2025-11-18

### Fixed
- Docs page unable to load correctly due to dependency mismatch
- Removal commands added to the Dockerfile resulted in unwanted "broken behavior related to SSL

## [0.17.0] - 2025-11-18

### Added
- New "Settings" table in the database with a corresponding `get_settings()` method to fetch.
- Added a new "provider_id" feature to the tracks table in the database
- New classes for the In/Out of Garrison rule, which is part of the Inference Sensemaker, so that necessary computational data can be retrieved all at once with a custom SDK query
- Added one index to `points` table to prevent long-running Geo query that compounded with each call.
- Added new setting input schema validation and get method for use in the endpoint

### Changed
- Tracks are now separated by provider
- Encrypted whitelist of endpoints to be secret in repo

### Fixed
- Latest DB migration refers to correct parent migration

### Removed
- Unused OS level packages from the Sensemaking Docker image which were requested to be addressed (removed/updated) by the DevOPs team

## [0.16.0] - 2025-11-03

### Added
- New API endpoint to view Audit Error Logs which get saved to the DB
- New classes for getting attributes used for enriching MilSymbols all at once

### Changed
- Changed formatting of logging statements from f-string to lazy logging % format
- Sensemakers now run on all split tracks which are generated

### Fixed
- Centralized the instantiation of the database engine and session (`clients/instances.py`) to improve geo-sensemaker performance.
- Pulled out unnecessary processing from thread locks in Geo controller, while maintaining safety of buffers.
- Sync client unable to connect due to CA File ssl auth errors

### Removed

## [0.15.0] - 2025-10-21

### Added
- Async OMS Client
- Ensure automated tests have 80% coverage
- Added Pydantic models and a TypeAdapter to validate the `audit_log_error_acm` loaded from JSON.
- OpenTelemetry integration for queue processing time and event counting metrics
- Filter Mil Symbol Attribute Inputs based on IRI before we rehydrate them

### Changed
- Removed Postgres Client and EPEL repository installation in Dockerfile
- Updated ATOMS dependency to Grimlock-INC-33

### Fixed

- Fixed `make nuke` target so that it now purges all volumes associated with oms-sensemaking.
- Corrected the Jenkins build job for the Sensemaking image which occasionally created incorrect versions
- Allow test coverage portion of the Jenkins pipeline to run and post results to SonarQube in AIDE
- Fixed MilSymbol Sensemaker bug where an invalid character part of a symbol Id code would be processed and cause errors in the service
- Fixed issue with the open telemetry unit tests not work properly when the services weren't running

### Removed

## [0.14.0] - 2025-09-29

### Fixed
- Improved on failing integration tests for the crud tool.

### Removed
- Removed "localstack" docker container and other references.

## [0.13.1] - 2025-09-19

### Added
- Ontology Service

### Changed
- Reverted In or Out of Garrison custom query

## [0.13.0] - 2025-09-16

### Added
- Implemented IP logging to meet V-222470 standards
- Added more unit tests to the code base to achieve a code coverage of at least 80%

### Changed
- Integrate custom query in InOrOutOfGarrison to reduce complexity.
- Refactored code in compliance to SonarQube scans
- Updated logs to not print potentially classified data
- Replaced geolib with pygeohash and updated python and system packages to mitigate some prisma issues
- Separated CACERT_PATH into AAC_CACERT_PATH and ATOMS_CACERT_PATH

### Fixed
- Issues with parsing certain envvars within the .env
- Issue with loading Swagger Docs content

## [0.12.1] - 2025-09-09

### Fixed
- Incorrect pgsql version being added to PATH was updated to version 17 to commincate with the database in deployed environments

## [0.12.0] - 2025-09-08

### Added
- Log request header information
- Added authorization for POST /aac/clear endpoint

### Changed
- Dockerfile and related build files are now ready to build UBI8 based images for Sensemaking in the AIDE environment
- Changed the SwaggerUI imports to be the static local versions instead of online imports
- Only use private pypi package registries
- Updated Sensemaking's Postgres version to 17 for the local dev environment and client installed in the Docker image
- Reverted Incursion rule code to read areas of interest files from a directory instead of raw string paths
- Updated ATOMS dependency to Grimlock-INC-30

### Fixed
- Fixed bug causing multiple incursions to be created

### Removed
Removed the NLP feature from the code base to comply with STIG V-222518

## [0.11.1] - 2025-08-25

### Added

### Changed

### Fixed
- Had to change structure of how area of interest files are read due to helm chart conflict

### Removed

## [0.11.0] - 2025-08-25

### Added
- Capabilities for the Incursion rule to read in .kml/.kmz formatted files as areas of interest
- Logic for processing search queries in the Observable Sensemaker
- Added timestamps to fast api log

### Changed
- Incursion rule now reads areas of interest files from a directory in bulk
- Certain Incursion rule logic was moved into models and classes for improved readability and future development
- Updated ATOMS dependency to Grimlock-INC-29

### Fixed

### Removed
- Unused data directory

## [0.10.0] - 2025-08-11

### Added
- Endpoint to clear Local AAC Cache
- Script to create transfer bundles
- CronEventEmitter, which emits fake Audit Log Events on a set interval
- Observable Sensemaker, which processes all observables every 15 minutes
- Implemented geofence logic, other observable types to be implemented

### Changed
- Updated Inference Sensemaker to only accept Observation Audit Log Events
- Attach Sensemaking generated "Incursion" attribute to its correlated activity instead
the "incurring" node.
- Removed the "v" prefix from version identifiers
- Changed Sensemaking Docker image to a UBI8/RHEL8 based image
- Updated `docker/postgis/initdb.d` scripts to use environment variables rather than hard-coded values. Refactored `.sql` scripts to `.sh` scripts.
- Custom Classification Bars
- DOD Consent Popup

### Changed

### Fixed
- SSL issues with AAC cache transport

### Removed

## [0.9.0] - 2025-07-28

### Added
- Out of Garrison automated smoke test

### Changed

### Fixed
- RDF Endpoint requires `user_dn` passed in requests
- AAC Cache transport missing ssl context

### Removed

## [0.8.1] - 2025-07-16

### Added

### Changed
- Updated OMS dependency to Grimlock-INC-25
- Use separate clients for AAC caching

### Fixed

### Removed

## [0.8.0] - 2025-07-14

### Added
- Added AuditLogError database table to store errors
- Expanded further on Mil Symbol configuration to encompass various symbol Id formats found high side
- Added the ability for the Mil Symbol sensemaker to enrich echelon in symbol Id codes

### Changed

### Fixed
- Listed ES as ASOMS dependency
- No longer incorrectly throw errors when dealing with observations with no start time/end time
- AAC Cache handles acm rollup requests

### Removed

## [0.7.4] - 2025-06-26

### Added
- New rate limit decorator functions for OMS crud tool to throttle OMS API requests
- AAC requests are cached
- Limit queue messages being actively processed

### Changed
- Updated Garrison rule to use the Facility's geometry to determine whether new points are part of existing or new Garrison Activity

## [0.7.3] - 2025-06-24

### Added
- Mil Symbol sensemaker can now handle symbol modifier codes for 2525B and 2525C

### Fixed
- Out of Garrison location query uses the garrison id directly

### Removed
- Unused placeholder semantic api and sensemaker

## [0.7.2] - 2025-06-18

### Fixed
- Incursion Activity description no longer exceeds OMS max field length

## [0.7.1] - 2025-06-13

### Added
- Track Weaver algorithm can be set through configuration

## [0.7.0] - 2025-06-13

### Added
- Added two helper methods to the Resolution sensemaker and created the AttributeCombinations and Criteria helper classes for resolution sensemaker
- RDF endpoint displays relationships to objects
- Mil Symbol sensemaker additionally checks for attributeIri in determining starting Mil symbol code

### Changed
- Updated OMS dependency to Grimlock-INC-23

### Fixed
- Fixed the Resolution sensemaker's inability to process multiple attributes used for identifying duplicates
- Handling connection errors with RabbitMQ
- Made Mil Symbol logic user uppercase values to make config lookups case insensitive
- Removed unnecessary Add Has Name Attribute rule from Inference Sensemaker

## [0.6.1] - 2025-05-21

### Added
- Elasticsearch and ESS added to the docker-compose setup

### Changed
- Updated Python to 3.12.10

### Fixed
- Fixed error with single point tracks

## [0.6.0] - 2025-05-20

### Added
- Added MIL-STD-2525B Support

### Changed
- Updated OMS dependency to Grimlock-INC-21

### Fixed
- Fixed bug where exceptions in RabbitMQListeners would cause excessive requests to core
- Fixed bug where empty attribute values would be matched by resolution sensemaker
- Fixed bug where resolution sensemaker would match with incomplete lists

## [0.5.0] - 2025-05-07

### Added
- Tracks are split when occurring longer than a configurable max timeframe
- Queue Event logs include Queue Name
- Track LineString geometries crossing antimeridian are split into a MultiLineString
containing the segments to the left and right of the antimeridian

### Changed
- Switched from SQS to RabbitMQ consumption
- Updated Geosensemakers to use settings based on IRI from config
- Updated OMS dependency to Grimlock-INC-19

### Fixed

## [0.4.0] - 2025-04-17

### Added
- Added documentation for the Mil Symbol Sensemaker
- Updated NSO Resolution to use average colocation difference to determine duplicates
- Common sense filtering by node IRI
- Push Track Observations to the OMS API

### Changed
- Updated OMS dependency to Grimlock-INC-18

### Fixed
- AAC Client requests failing for Geospatial Sensemakers

## [0.3.1] - 2025-04-11

### Added
- Updated Cotravel Sensemaker to catch potential duplicate nodes for NSO Resolution
- Added omsb-init container to docker compose
- Duplicate object checks in the Resolution sensemaker are now configurable
- Added CA Cert argument to AAC Client

### Changed
- Geosensemakers get runtime configs per node IRI based on geo_sensemaker_config.json file
- Docker tag version number has missing `v`
- Changed Grimlock version from 14 to 17
- Updated Sensemaking smoke tests
- Updated Sensemaking to be compatibale with breaking changes
from Grimlock 17 (IRIs, ActivityState, altered object labels)

## [0.3.0] - 2025-04-03

### Added
- None

### Changed
- Now serving documentation at "/" instead of version information.

## [0.2.0] - 2025-03-20

> *Galadriel-INC-2*

### Added
- Mil Symbol now updates the node's symbolIdCode with the 2525-C SDIC
- Mil Symbol enrichment can now look at controlling parent node's affiliation

### Changed
- None


## [0.1.0] - 2025-03-06

> *Galadriel-INC-1*

### Added
- None

### Changed
- None
