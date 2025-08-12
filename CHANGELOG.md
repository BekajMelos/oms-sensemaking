# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

### Added
- Async OMS Client

### Changed

### Fixed

### Removed

## [0.10.0] - 2025-08-11

### Added
- Endpoint to clear Local AAC Cache
- Script to create transfer bundles

### Changed
- Updated Inference Sensemaker to only accept Observation Audit Log Events
- Attach Sensemaking generated "Incursion" attribute to its correlated activity instead
the "incurring" node.
- Removed the "v" prefix from version identifiers
- Changed Sensemaking Docker image to a UBI8/RHEL8 based image

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
- Updated Garrison rule to use the Facility's goemetry to determine whether new points are part of existing or new Garrison Activity

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
- Removed unneccesary Add Has Name Attribute rule from Inference Sensemaker

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
