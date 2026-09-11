# Changelog

All notable changes to **Domoticz-MySkodaAPI** are documented in this file.

The project follows [Semantic Versioning](https://semver.org/) where practical.

* **Alpha** releases are development releases and may contain architectural or device-model changes.
* **Beta** releases are intended for real-world use but may still introduce changes before `1.0.0`.
* **`1.0.0`** will mark the first production-stable release with a frozen device model and a strong commitment to upgrade compatibility.

---

# Release History

## [0.4.2] - 2026-09-11

### Changed

* Production cleanup release based on `0.4.1`.
* The 44 devices are no longer dropped/recreated on launch. 
* Redesign of the device.py 
* Documentation was aligned with the actual `0.4.2` plugin configuration and device model.
* Domoticz units `1–44` remain unchanged.
* The read-only telemetry model remains unchanged.

## [0.4.1] - 2026-09-08

### First Stable Beta

The first release considered suitable for longer-running real-world use.

### Changed

* Production cleanup release based on `0.4.0-alpha.3`.
* API Status now includes the HTTP return code.
* API Status also reports the RFC problem type when supplied by the MyŠkoda API, including:

  * `rate-limit-exceeded`
  * `vehicle-not-accepting-requests`
* Documentation was aligned with the actual `0.4.1` plugin configuration and device model.
* Domoticz units `1–44` remain unchanged.
* The read-only telemetry model remains unchanged.

### Repository

* Added repository hygiene rules for:

  * runtime state
  * generated archives
  * Python cache files
  * local editor files

### Compatibility

* Existing Domoticz unit numbers are preserved.
* No vehicle commands are sent to MyŠkoda.
* Existing installations can continue using the established telemetry model.

### Known Issues

* Changing Domoticz device characteristics during an upgrade can still cause the plugin to crash in some circumstances.
* Device migration and device-type changes therefore require additional hardening before the project can be considered production-stable.

See GitHub issue #6 for the current device-type migration problem.

---

## [0.4.0-alpha.3] - 2026-09-05

### Added

* Added unit `44` — **API Key Status**.

* Implemented the sensor as a native Domoticz General/Alert sensor.

* Added API-key status levels:

  * `OK`
  * `WARNING`
  * `EXPIRED`
  * `UNKNOWN`

* Added configurable warning threshold through:

  `API_KEY_EXPIRY_WARNING_DAYS`

* Default warning threshold is **30 days**.

### Compatibility

* Unit `21` — **API Key Expiry** remains available as a numeric days-remaining Custom Sensor.
* Existing device units remain unchanged.

---

## [0.4.0-alpha.2] - 2026-09-05

### Changed

* Vehicle Captured is now represented as elapsed seconds since the vehicle capture timestamp supplied by the API.
* API Key Expiry is now represented as numeric days remaining.
* Added configurable API-key expiry warning threshold.
* Default warning threshold is 30 days.
* API Status now includes the HTTP return code and its meaning.

### Added

* Unit `42` — **API Rate Remaining**.
* Unit `43` — **API Rate Reset In**.

---

## [0.4.0-alpha.1]

### Changed

* Replaced semantic Text state devices with native Domoticz Selector Switch devices for vehicle-state telemetry.
* Preserved existing Domoticz unit numbers `1–41`.
* Added automatic migration for affected existing devices.
* Selector Switch controls remain telemetry-only.
* Selector controls do **not** send commands to the vehicle.

### Added

* Target Temperature is represented as a read-only Domoticz Custom Sensor.
* Target Temperature uses degrees Celsius (`°C`).

### Design Principle

The Selector Switch implementation provides a native Domoticz representation of vehicle states while deliberately keeping the integration read-only.

---

## [0.3.0-alpha4] - 2026-09-05

### Release

* Released the `0.3.0-alpha4` development milestone.
* Continued the transition toward a more complete and structured vehicle telemetry model.

### Note

This release formed part of the rapid architecture and telemetry development leading to the `0.4.x` beta series.

---

## [0.0.4-alpha]

### Added

Expanded the normalized vehicle telemetry model with:

* charging state
* battery state of charge
* electric range
* charging connection
* target state of charge
* charge mode where supported
* engine/fuel type
* telemetry capture timestamps
* API partial-data error reporting
* API capability summary
* supported-operation reporting

### Design

* Integration remains read-only.
* No vehicle commands are issued.

---

## [0.0.3.5-alpha.4]

### Changed

* Changed **Fuel Range** to a Domoticz Custom Sensor.
* Changed **Total Range** to a Domoticz Custom Sensor.
* Explicitly use `km` as the unit.
* Preserved existing Domoticz unit numbers.

---

## [0.0.3.5-alpha.3]

### Added

* Added Custom Sensor handling for range values.
* Added migration support for affected Domoticz devices.

---

## [0.0.3.5-alpha.2]

### Added

* Added semantic smart-state handling for vehicle telemetry.
* Improved the interpretation of vehicle state values before publishing them to Domoticz.

---

## [0.0.3.5-alpha.1]

### Added

* Added persistent odometer state.
* Added daily distance delta calculation.
* Added **Today's Distance**.
* Added **Yesterday's Distance**.

### Changed

* Completed daily distance is rolled into Yesterday Distance at local midnight.
* Negative odometer changes are ignored.
* Implausibly large odometer jumps are ignored.

### Design

The plugin now maintains a small amount of local state in order to provide useful derived vehicle information rather than simply exposing raw API values.

---

## [0.0.3.5-alpha]

### Changed

* Improved Domoticz device types.
* Improved telemetry presentation.
* Continued migration toward semantically correct Domoticz devices.

---

## [0.0.3-alpha.1]

### Fixed

* Corrected MyŠkoda Public API authentication to use:

  `X-API-Key`

* Corrected parsing of the current MyŠkoda API response under the `vehicle` object.

### Added

* API-key expiry header parsing.
* API rate-limit response header parsing.

---

## [0.0.3-alpha]

### Added

* HTTP `429` retry handling.
* Transient HTTP `5xx` retry handling.
* `Retry-After` support.
* Exponential backoff.
* API error classification.
* API rate-limit metadata.
* Last-known-good vehicle-state caching.

### Compatibility

* Existing Domoticz unit IDs remain unchanged.

### Reliability

Temporary MyŠkoda API failures no longer have to result in immediate loss of the previously known vehicle state.

---

## [0.0.2-alpha]

### Architecture

Introduced the refactored plugin architecture with separate responsibilities for:

* API communication
* vehicle-state processing
* Domoticz device management
* utilities
* constants

### Compatibility

* Preserved the original Domoticz units `1–23`.

### Design

* Integration remains read-only.
* Project remains standard-library based.
* API and Domoticz responsibilities are separated to allow future expansion.

---

## [0.0.1.1-alpha] - 2026-09-04

### Development Release

* First intermediate development release following the initial beta.
* Established the foundation for the subsequent API, telemetry and architecture refactoring.

---

## [0.0.1-beta] - 2026-09-02

### First Long-Running Beta

* Adjusted Domoticz device definitions.
* Established the first long-running beta implementation.
* Began the transition from an experimental integration toward a continuously running Domoticz plugin.

---

# Current Status

## 0.4.1 — First Stable Beta

The project currently provides a **read-only MyŠkoda telemetry integration for Domoticz**.

The current architecture includes:

* MyŠkoda API communication
* API-key authentication
* retry and backoff handling
* rate-limit handling
* last-known-good state handling
* normalized vehicle telemetry
* battery information
* charging information
* fuel and range information
* odometer tracking
* daily distance calculation
* vehicle-state telemetry
* climate-related telemetry
* API diagnostics
* API-key expiry monitoring
* API rate-limit monitoring
* native Domoticz device types
* device migration support
* stable Domoticz unit numbering

The project currently remains **read-only** with respect to the vehicle.

---

# Versioning Policy

The project uses Semantic Versioning where practical.

* Patch releases (`x.y.Z`) are intended for fixes, documentation corrections and maintenance.
* Minor releases (`x.Y.0`) may introduce new functionality while maintaining the established architecture and compatibility expectations.
* Alpha releases may introduce device-model or architectural changes.
* Beta releases should be suitable for real-world use but may still introduce changes before `1.0.0`.
* `1.0.0` will represent the first production-stable release with a frozen device model and a strong commitment to upgrade compatibility.

---

