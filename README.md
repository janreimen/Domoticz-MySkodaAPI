
MySkoda API Integration for Domoticz

**Version 0.4.2**

A read-only Domoticz Python plugin for the official Škoda MySkoda Public API.

## Highlights

- Read-only vehicle telemetry; no remote vehicle commands are sent.
- Authentication with the API's `X-API-Key` header.
- Current API response format with `vehicle` data and optional partial-response `errors`.
- Retry handling for HTTP 429 and transient 5xx responses.
- `Retry-After` and exponential backoff support.
- Last-known-good vehicle state cache.
- API rate-limit and API-key expiry diagnostics.
- RFC-style API problem types exposed in API Status when supplied by the API.
- Native Domoticz selector devices for semantic states.
- Native Domoticz Alert sensor for API-key health.
- Daily and previous-day distance tracking.
- Charging, battery, climate, security, fuel and telemetry diagnostics.
- Python standard library only; no third-party runtime dependencies.
- Existing Domoticz units 1–44 are preserved for upgrade compatibility.

## Requirements

- Domoticz with Python plugin support (2026.3 tested).
- Python 3.
- A valid MySkoda API key.
- The vehicle VIN.
- Network access from Domoticz to the MySkoda API.

No third-party Python package is required by the plugin.

## Installation

Copy the complete plugin directory into the Domoticz `plugins` directory:

```text
<domoticz>/plugins/Domoticz-MySkodaAPI/
```

The directory must contain `plugin.py` and the supporting Python modules shipped with this release.

Restart Domoticz after installing or replacing the plugin.

## Configure the Domoticz hardware

Add a new hardware instance for **MySkoda API Integration**.

The plugin configuration fields are:

| Field | Description |
|---|---|
| API Key | MySkoda Public API key; stored by Domoticz as a password field |
| VIN | Vehicle VIN |
| Poll Interval (minutes) | Polling interval, default 30 minutes; accepted range 15–60 minutes |
| Debug | Off, Basic or Verbose |

The plugin is intentionally **read-only**. Selector devices are telemetry displays, not controls. Commands from Domoticz are rejected and the selector is restored to the API-reported state.

## Device units

The plugin deliberately keeps the established unit numbers:

| Unit | Device |
|---:|---|
| 1 | Vehicle |
| 2 | Doors Locked |
| 3 | Doors |
| 4 | Windows |
| 5 | Lights |
| 6 | Trunk |
| 7 | Bonnet |
| 8 | Sunroof |
| 9 | Fuel Level |
| 10 | Fuel Range |
| 11 | Total Range |
| 12 | Odometer / Mileage |
| 13 | Vehicle State |
| 14 | Parking Address |
| 15 | Parking GPS |
| 16 | Air Conditioning |
| 17 | Target Temperature |
| 18 | Auxiliary Heating |
| 19 | Active Ventilation |
| 20 | Vehicle Captured |
| 21 | API Key Expiry |
| 22 | API Rate Limit |
| 23 | API Status |
| 24 | Today Distance |
| 25 | Yesterday Distance |
| 26 | Vehicle Security |
| 27 | Climate State |
| 28 | Data Quality |
| 29 | Fuel / Engine Type |
| 30 | Charging State |
| 31 | Battery SoC |
| 32 | Electric Range |
| 33 | Charging Connected |
| 34 | Charge Target |
| 35 | Charge Mode |
| 36 | Charging Captured |
| 37 | Fuel Captured |
| 38 | Odometer Captured |
| 39 | API Capabilities |
| 40 | API Data Errors |
| 41 | Supported Operations |
| 42 | API Rate Remaining |
| 43 | API Rate Reset In |
| 44 | API Key Status |

### Unit 44 — API Key Status

Unit 44 is a native Domoticz General/Alert sensor:

- **Green** — API key OK.
- **Yellow** — API key expires within the warning threshold.
- **Red** — API key expired.
- **Gray** — expiry status is unknown.

The default warning threshold is **30 days** (`API_KEY_EXPIRY_WARNING_DAYS`).

### API diagnostics

- **Unit 21 — API Key Expiry:** numeric days remaining.
- **Unit 22 — API Rate Limit:** API request limit reported/used by the integration.
- **Unit 23 — API Status:** HTTP status code and meaning; includes the short RFC problem type when the API supplies one.
- **Unit 40 — API Data Errors:** partial-response/API data errors.
- **Unit 42 — API Rate Remaining:** remaining requests in the current rate-limit window.
- **Unit 43 — API Rate Reset In:** seconds until the rate-limit quota resets.
- **Unit 44 — API Key Status:** visual API-key health.

## API behavior

The plugin retrieves vehicle data using:

```text
GET https://public.api.connect.skoda-auto.cz/api/v1/vehicles/{vin}
```

Authentication is sent as:

```text
X-API-Key: <your-api-key>
```

The integration also consumes API response headers such as API-key expiry and rate-limit information when available.

Transient failures are retried. HTTP 429 and server-side 5xx responses use bounded retry/backoff logic, and `Retry-After` is honored when supplied.

A successful HTTP 200 response may still contain partial-data errors. Such errors do not automatically invalidate usable vehicle data.

## Runtime state and repository hygiene

The plugin creates local runtime state files for caching and distance tracking. These are **runtime files, not release files**, and must not be committed to Git.

The repository `.gitignore` excludes:

```text
myskoda_last_state.json
myskoda_distance_state.json
*_state.json
*.state.json
__pycache__/
*.py[cod]
.pytest_cache/
*.swp
*.swo
```

Never commit:

- API keys or credentials.
- Private vehicle information.
- Runtime JSON state files.
- Local backups or `archive/` material.
- Logs containing sensitive data.

If sensitive files were already committed, deleting them in a new commit does **not** remove them from Git history. Rewrite the repository history and rotate/revoke any exposed credentials.

## Development and tests

The project contains a lightweight test suite in `tests.py`.

Run it in an environment where the Domoticz Python plugin API is available:

```bash
python3 tests.py
```

For a basic source-tree syntax check without Domoticz, use:

```bash
python3 -m py_compile *.py
```

## Release checklist

Before publishing a release:

```bash
git status --short --ignored
git add .
git status
git commit -m "Release 0.4.1"
git tag -a 0.4.1 -m "Release 0.4.1"
```

Then push the actual repository branch and tag:

```bash
git push origin <branch>
git push origin 0.4.1
```

Do not assume the branch is `master` or `main`; check with:

```bash
git branch --show-current
```

The published source tree must not contain `archive/` or runtime state JSON files.

## Security

See [`SECURITY.md`](SECURITY.md) for vulnerability reporting and secret-handling guidance.

## License

MIT License. See [`LICENSE`](LICENSE).

## Official API documentation

Škoda MySkoda Public API documentation:

https://public.api.connect.skoda-auto.cz/docs
