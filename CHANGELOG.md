# Changelog

## 0.0.3-alpha

### Added
- Robust API retry handling for HTTP 429 and transient 5xx responses.
- `Retry-After` handling.
- Exponential backoff for transient connection errors.
- API error classification.
- Rate-limit metadata reporting.
- Persistent last-known-good vehicle-state cache.
- Failure handling that preserves valid Domoticz values.
- Additional parser and API metadata tests.

### Changed
- Polling now backs off after failures instead of hammering the API.
- Existing Domoticz unit IDs 1–23 remain unchanged.
- API key is never included in diagnostic output or state cache.

### Unchanged
- Read-only operation.
- Direct official MySkoda API access.
- Python standard library only.
