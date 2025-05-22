# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

### Added

### Changed

### Fixed

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
- Mil Symbol sensemaker additionally checks for attributeIri in determining starting Mil symbol code

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
