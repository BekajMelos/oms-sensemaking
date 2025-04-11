# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

### Added
- Updated Cotravel Sensemaker to catch potential duplicate nodes for NSO Resolution
- Added omsb-init container to docker compose
- Duplicate object checks in the Resolution sensemaker are now configurable
- Added CA Cert argument to AAC Client

### Changed
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



[Unreleased]: https://tex.gerbil-cloud.ts.net:3000/oms/oms-sensemaking/compare/v0.3.0...main
[0.3.0]: https://tex.gerbil-cloud.ts.net:3000/oms/oms-sensemaking/releases/tag/v0.3.0
[0.2.0]: https://tex.gerbil-cloud.ts.net:3000/oms/oms-sensemaking/releases/tag/v0.2.0
[0.1.0]: https://tex.gerbil-cloud.ts.net:3000/oms/oms-sensemaking/releases/tag/v0.1.0
