# MySkoda API Integration for Domoticz

**Version: 0.0.3.5-alpha.4**

A read-only Domoticz Python plugin using the official Škoda MySkoda Public API directly.

Repository: https://github.com/janreimen/Domoticz-MySkodaAPI

## 0.0.3.5-alpha.1

This release builds on the 0.0.2-alpha architecture/refactor and concentrates on reliability:

- transient HTTP retry handling for 429/5xx responses
- `Retry-After` support
- exponential backoff for connection/transient failures
- API status classification (`OK`, `AUTH_ERROR`, `RATE_LIMITED`, `API_ERROR`, `CONNECTION_ERROR`, `INVALID_DATA`)
- rate-limit metadata exposed through the existing Domoticz device
- last-known-good vehicle state persisted locally
- temporary API failures do not erase the last valid vehicle values
- retry/backoff after repeated failures
- API key is never written to logs or cache
- existing Domoticz unit IDs 1–23 are preserved
- standard-library-only implementation

## Requirements

- Domoticz with Python plugin support
- Python 3
- Škoda vehicle supported by the MySkoda Public API
- MySkoda account
- MySkoda Public API key
- vehicle VIN

No third-party Python package is required.

## Installation

For an existing installation, replace the plugin files in the existing directory rather than deleting/recreating the Domoticz hardware. This preserves the existing device units.

Typical installation path:

```text
/srv/domoticz/plugins/Domoticz-MySkodaAPI
```

After replacing the files:

```bash
cd /srv/domoticz/plugins/Domoticz-MySkodaAPI
python3 -m py_compile plugin.py devices.py myskoda_api.py vehicle.py constants.py utils.py tests.py
python3 tests.py
sudo systemctl restart domoticz
```

## Configuration

- API Key: your MySkoda Public API key
- VIN: vehicle VIN
- Poll Interval: 15–60 minutes; default 30
- Debug: Off / Basic / Verbose

The plugin remains read-only in 0.0.3.5-alpha.1. It does not send commands to the vehicle.

## State cache

The plugin stores the last successfully parsed vehicle state in `myskoda_last_state.json` under the Domoticz plugin home. It is used only as a last-known-good state and does not contain the API key.

## Existing Domoticz units

The following unit numbers remain unchanged from earlier versions:

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
| 12 | Odometer |
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

## Security

Never paste the API key into an issue, log, screenshot, Git repository, or public configuration file.

See `SECURITY.md` for reporting security issues.


## Daily distance counters (0.0.3.5-alpha.1)

The plugin keeps a persistent odometer baseline and calculates positive odometer deltas between successful API readings. It exposes:

- **Odometer** — custom Domoticz distance counter in km.
- **Today Distance** — accumulated driven distance for the current local calendar day.
- **Yesterday Distance** — the completed previous day's accumulated distance.

The baseline is stored in `myskoda_distance_state.json` in the Domoticz plugin HomeFolder. Plugin restarts do not reset the current day's distance. Negative or implausibly large odometer jumps are ignored.


## Smart states (0.0.3.5-alpha.4)

The plugin exposes semantic, read-only state sensors. These are intentionally Text devices so dashboard clicks cannot become vehicle commands.

- **Vehicle Security:** `SECURE`, `ATTENTION`, `UNKNOWN`
- **Climate State:** `OFF`, `CLIMATE`, `HEATING`, `VENTILATION`, `UNKNOWN`
- **Data Quality:** `GOOD`, `STALE`, `ERROR`, `UNKNOWN`

When the API temporarily fails, the last-known-good vehicle state is retained and Data Quality changes to `STALE`. The plugin does not replace valid vehicle values with `UNKNOWN` merely because a polling request failed.
