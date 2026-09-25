MySkoda API Integration for Domoticz

**Version 0.4.3.1-003-alpha**

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
- Daily and previous-day distance tracking as informational Custom Sensors; cumulative distance statistics remain on the odometer counter (unit 12).
- Charging, battery, climate, security, fuel and telemetry diagnostics.
- Charging power, remaining charging time and charge type (AC/DC), sourced from the same charging data already polled - no extra API call.
- Python standard library only; no third-party runtime dependencies.
- Existing Domoticz units 1–44 are preserved for upgrade compatibility; units 45–47 are new in 0.4.3.1-001-alpha, unit 48 in 0.4.3.1-003-alpha.

## Requirements

- Domoticz with Python plugin support (2026.3 tested).
- Python 3.
- A valid MySkoda API key.
- The vehicle VIN.
- Network access from Domoticz to the MySkoda API.

No third-party Python package is required by the plugin.

## Supported vehicles

The plugin talks to the same `vehicles/{vin}` MySkoda Public API endpoint for every model, so it should work for any Škoda in principle. This table tracks which models have actually been exercised against real API responses, versus ones still assumed to work.

| Model | Code | Status |
|---|---|---|
| Octavia 4 Facelift | NX | In development |
| Kodiaq II PHEV | PS | In development |
| Karoq Sportline 2.0 TFSI 140kW (MY2020) | NU | In development |

- **Checked** — confirmed against a real captured API response for that model/powertrain.
- **In development** — plugin is expected to work, but the raw API shape for this specific model/powertrain hasn't been confirmed yet; if you hit missing/zero values, please open an issue with a raw `charging`/`fuelStatus` dump (see [`verify_charging_fields.py`](./verify_charging_fields.py)).

### Known-compatible models (not yet tried with this plugin)

Škoda's own MyŠkoda app description states which models currently have MyŠkoda/Škoda Connect support at all - a prerequisite for reaching the API this plugin uses, independent of whether anyone has confirmed the exact JSON shape for it. Nobody has tested these with this plugin yet, so treat them as "should work" rather than verified; the model codes below are left blank rather than guessed - please open a PR or issue if you can confirm one.

| Model | Code | Source |
|---|---|---|
| Enyaq / Enyaq Coupé | — | Škoda MyŠkoda app description |
| Elroq | — | Škoda MyŠkoda app description; confirmed at launch (Dec 2024 press release) |
| Scala | — | Škoda MyŠkoda app description |
| Kamiq | — | Škoda MyŠkoda app description |
| Fabia (4th generation) | — | Škoda MyŠkoda app description |
| Octavia iV (PHEV) | NX | Škoda MyŠkoda app description; same body/code as the Octavia 4 Facelift above, different powertrain |
| Superb / Superb iV (PHEV) | — | Škoda MyŠkoda app description |
| Karoq (produced late 2020 onward) | — | Škoda MyŠkoda app description; note this plugin's own Karoq test above is a specific MY2020 unit, not a blanket confirmation for the whole model line |

Not listed because Škoda's own description doesn't claim MyŠkoda support for them: any Škoda older than roughly the early-2020s connected-services rollout (older Fabia/Rapid/Yeti/Citigo generations, pre-2020 Karoq, etc.). If your car isn't in either table, the safest first step is confirming it actually has MyŠkoda app connectivity before troubleshooting the plugin itself.

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
| 12 | Odometer / Mileage — cumulative RFXMeter counter used for Domoticz statistics |
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
| 24 | Today Distance — informational Custom Sensor; resets at local midnight |
| 25 | Yesterday Distance — informational Custom Sensor; previous completed day |
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
| 45 | Charging Power |
| 46 | Remaining Charging Time |
| 47 | Charge Type |

### Distance tracking and Domoticz statistics

- **Unit 12 — Odometer / Mileage** remains the cumulative RFXMeter counter. It must only move upward (apart from a genuine odometer reset) and is the distance source for Domoticz daily/monthly/yearly statistics.
- **Unit 24 — Today Distance** is an informational Custom Sensor and resets to zero at local midnight.
- **Unit 25 — Yesterday Distance** is an informational Custom Sensor containing the completed previous day.
- Units 24 and 25 are deliberately not RFXMeter counters, preventing negative midnight counter deltas.

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

### Units 45–47 — Charging diagnostics (0.4.3.1-001-alpha)

- **Unit 45 — Charging Power:** current charging power in kW.
- **Unit 46 — Remaining Charging Time:** minutes until fully charged.
- **Unit 47 — Charge Type:** `AC` or `DC`.

These are parsed from the `charging` object already fetched for units 30–35; no new API call or `API_INCLUDE` entry was needed.

The JSON field names used to extract these three values were not available in the published API documentation at the time of writing and have not yet been confirmed against a live response for every vehicle/account. Run `python3 verify_charging_fields.py <API_KEY> <VIN>` once (see "Development and tests" below) to confirm the field names for your vehicle before relying on these units; if they don't match, add the real key names to the candidate lists in `vehicle.py`.

### Unit 48 — Plug Lock State (0.4.3.1-003-alpha)

- **Unit 48 — Plug Lock State:** `Locked` or `Unlocked`, from the API's `plugLockState` field.

Added following the MySkoda API's v1.1.0 release, which introduced two new optional fields under `charging.status`:

- **`plugConnectionState`** (`CONNECTED`/`DISCONNECTED`) - now the preferred, authoritative source for **Unit 33 — Charging Connected**, used ahead of the older heuristic that inferred it from the derived charging state. That heuristic is kept as a fallback for responses without this field.
- **`plugLockState`** (`LOCKED`/`UNLOCKED`) - new information with no prior equivalent, exposed as Unit 48 above.

The v1.1.0 release notes also clarify two things about the *derived* charging state (`charging.status.state` - `CONNECT_CABLE`, `CHARGING`, `READY_FOR_CHARGING`, etc.): an omitted value never means the plug was reported as disconnected, and new values may be added over time. Both were already true of this plugin's fallback logic (it only acts on states it explicitly recognizes, and never infers "disconnected" from an absent state) - no behavior change was needed there, only confirmation.

Both new fields are optional, so vehicles/accounts on an older API revision will simply have `charging_connected` fall back to the existing heuristic and `plug_lock_state` stay `Unknown`.

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

`verify_charging_fields.py` is a standalone helper (no Domoticz dependency) that fetches one real API response and checks the raw `charging` object against the field-name candidates used for units 45–47, plus the v1.1.0 `plugConnectionState`/`plugLockState` fields used by units 33/48:

```bash
python3 verify_charging_fields.py <API_KEY> <VIN>
```

## Release checklist

Before publishing a release:

```bash
git status --short --ignored
git add .
git status
git commit -m "Release 0.4.3.1-003-alpha"
git tag -a 0.4.3.1-003-alpha -m "Release 0.4.3.1-003-alpha"
```

Then push the actual repository branch and tag:

```bash
git push origin <branch>
git push origin 0.4.3.1-003-alpha
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
