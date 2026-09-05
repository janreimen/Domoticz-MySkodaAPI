# Changelog

## 0.0.3.5-alpha.4

- Changed Fuel Range (unit 10) and Total Range (unit 11) to Domoticz Custom Sensor devices.
- Custom sensors use numeric values with `km` as the explicit custom unit.
- Avoids Domoticz Distance sensors displaying range values as centimetres.
- Existing unit numbers are preserved.


## 0.0.3.5-alpha.1

- Added custom km counters for Odometer, Today Distance and Yesterday Distance.
- Added persistent odometer delta state.
- Calculates positive distance deltas between successful readings.
- Rolls the completed day into Yesterday Distance at local midnight.
- Preserves the existing unit IDs 1-23 and adds units 24-25.
- Ignores negative and implausibly large odometer jumps.

# Changelog

## 0.0.3.5-alpha

### Fixed
- Corrected MySkoda Public API authentication to use the required `X-API-Key` header.
- Corrected parsing of the current API response structure under the `vehicle` object.
- Corrected parsing of current fuel, range, odometer, status, parking GPS and auxiliary-heating fields.
- Added parsing of `X-API-Key-Expires-At` and current `RateLimit-*` response headers.

### Tested
- Real API response shape from the current MySkoda Public API.
- Existing legacy/flat response parsing remains supported.
- API authentication path now matches the successful curl request.

## 0.0.3-alpha

### Added
- Robust API retry handling for HTTP 429 and transient 5xx responses.
- `Retry-After` handling.
- Exponential backoff for transient connection errors.
- API error classification.
- Rate-limit metadata reporting.
- Persistent last-known-good vehicle-state cache.
- Failure handling that preserves valid Domoticz values.

### Changed
- Polling backs off after failures instead of hammering the API.
- Existing Domoticz unit IDs 1–23 remain unchanged.
- API key is never included in diagnostic output or state cache.

## 0.0.3.5-alpha.2

### Added
- Smart read-only vehicle states for security, climate and data quality.
- Vehicle Security: `SECURE`, `ATTENTION`, `UNKNOWN`.
- Climate State: `OFF`, `CLIMATE`, `HEATING`, `VENTILATION`, `UNKNOWN`.
- Data Quality: `GOOD`, `STALE`, `ERROR`, `UNKNOWN`.
- New units 26-28 while preserving units 1-25.

### Changed
- Vehicle state devices are now read-only Text sensors rather than clickable Switch devices.
- Doors, windows, lights, trunk, bonnet, sunroof and climate states are normalized to semantic uppercase states.
- A temporary API failure keeps the last-known-good vehicle values while marking Data Quality as `STALE` (or `ERROR` if no cached state exists).
- Odometer/Mileage, Fuel Range and Total Range remain proper distance-oriented sensors/counters.
