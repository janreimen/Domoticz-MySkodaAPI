# Changelog

## 0.0.3-alpha.1

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
