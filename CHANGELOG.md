hangelog

All notable changes to the MySkoda API Integration for Domoticz are documented here.

## 0.4.1

- Production cleanup release based on 0.4.0-alpha.3.
- API Status now includes the HTTP return code and, when supplied by the MySkoda API, the RFC problem type (for example `rate-limit-exceeded` or `vehicle-not-accepting-requests`).
- Added repository hygiene rules for runtime state, archives, Python caches and local editor files.
- Kept Domoticz units 1–44 and the read-only telemetry model unchanged.
- Documentation aligned with the actual 0.4.1 plugin configuration and device model.

## 0.4.0-alpha.3

- Added unit 44 `API Key Status` as a native Domoticz General/Alert sensor.
- Alert levels: green `OK`, yellow `WARNING` at or below `API_KEY_EXPIRY_WARNING_DAYS` (default 30 days), red `EXPIRED`, gray `UNKNOWN`.
- Kept unit 21 `API Key Expiry` as a numeric days-remaining Custom Sensor.

## 0.4.0-alpha.2

- Vehicle Captured is now elapsed seconds since the API vehicle capture timestamp.
- API Key Expiry is now numeric days remaining, with configurable warning threshold `API_KEY_EXPIRY_WARNING_DAYS` (default 30 days).
- API Rate Remaining and API Rate Reset In are exposed as dedicated numeric sensors (units 42/43).
- API Status includes the HTTP return code and meaning.

## 0.4.0-alpha.1

- Replaced semantic Text state devices with native Domoticz Selector Switch devices for vehicle state telemetry.
- Preserved existing unit numbers 1–41 and migrated affected devices automatically.
- Selector controls are telemetry-only; no MySkoda vehicle commands are sent.
- Target Temperature is a read-only Custom Sensor in °C.

## 0.0.4-alpha

- Expanded the normalized vehicle telemetry model with charging, battery SoC, electric range, charging connection, target SoC and charge mode where supported.
- Added engine/fuel type, telemetry capture timestamps, API partial-data error reporting, API capability summary and supported-operation reporting.
- Remains read-only.

## 0.0.3.5-alpha.4

- Changed Fuel Range and Total Range to Domoticz Custom Sensor devices using explicit `km` units.
- Preserved existing unit numbers.

## 0.0.3.5-alpha.3

- Added Custom Sensor handling for range values and migration support for the affected Domoticz devices.

## 0.0.3.5-alpha.2

- Added semantic smart-state handling for vehicle telemetry.

## 0.0.3.5-alpha.1

- Added daily distance delta counters and persistent odometer state.
- Rolls completed daily distance into Yesterday Distance at local midnight.
- Ignores negative and implausibly large odometer jumps.

## 0.0.3.5-alpha

- Improved Domoticz device types and telemetry presentation.

## 0.0.3-alpha.1

- Corrected MySkoda Public API authentication to use `X-API-Key`.
- Corrected parsing of the current API response under the `vehicle` object.
- Added parsing of API-key expiry and rate-limit response headers.

## 0.0.3-alpha

- Added retry handling for HTTP 429 and transient 5xx responses.
- Added `Retry-After`, exponential backoff, API error classification, rate-limit metadata and last-known-good state caching.
- Existing Domoticz unit IDs remain unchanged.

## 0.0.2-alpha

- Introduced the refactored plugin architecture with separate API, vehicle-state, device-management and utility modules.
- Preserved the original Domoticz units 1–23.
- Kept the integration read-only and standard-library based.

