# Domoticz-MySkodaAPI

**MySkoda API Integration** for Domoticz.

- Version: **0.0.1-alpha**
- GitHub: https://www.github.com/janreimen/Domoticz-MySkodaAPI
- Author: Jan Reimen
- Initial target: Škoda Octavia 4.5 RS 265

## Repository / plugin structure

This repository **is the plugin directory**. There is no nested `plugins/` directory and no `plugin/` subdirectory.

```text
Domoticz-MySkodaAPI/
├── plugin.py
├── README.md
├── SECURITY.md
├── LICENSE
├── requirements.txt
└── .gitignore
```

For a normal Domoticz installation, the repository is deployed as one dedicated subdirectory below Domoticz's `plugins` directory:

```text
<domoticz>/plugins/MySkodaAPI/
├── plugin.py
├── README.md
├── SECURITY.md
├── LICENSE
├── requirements.txt
└── .gitignore
```

This follows Domoticz's Python plugin model: each plugin has its own directory and an entry-point `plugin.py`. Domoticz requires a restart after installing a Python plugin. citeturn0search0turn0search5

## Requirements

- Domoticz with Python plugin support enabled
- Python 3
- Internet access to `https://public.api.connect.skoda-auto.cz`
- A MyŠkoda API key
- A VIN authorized by that API key

Version `0.0.1-alpha` uses only Python standard-library modules; no `pip install` is required.

## Installation

### Linux / native Domoticz

```bash
cd /opt/domoticz/plugins
git clone https://www.github.com/janreimen/Domoticz-MySkodaAPI MySkodaAPI
sudo chown -R domoticz:domoticz MySkodaAPI
python3 -m py_compile MySkodaAPI/plugin.py
sudo systemctl restart domoticz
```

If the repository was downloaded as a ZIP, extract/copy its **root contents** into:

```text
/opt/domoticz/plugins/MySkodaAPI/
```

Do not create:

```text
/opt/domoticz/plugins/MySkodaAPI/plugins/
```

and do not create:

```text
/opt/domoticz/plugins/MySkodaAPI/plugin/plugin.py
```

The required entry point is:

```text
/opt/domoticz/plugins/MySkodaAPI/plugin.py
```

### Docker

For Docker, mount the repository root to the dedicated plugin directory inside the Domoticz container, for example:

```yaml
volumes:
  - /path/to/Domoticz-MySkodaAPI:/opt/domoticz/plugins/MySkodaAPI:ro
```

Do not mount it directly as `/opt/domoticz/plugins` because that can hide other plugins.

## Configure in Domoticz

After restarting Domoticz:

**Setup → Hardware → Add → MySkoda API Integration**

Configure:

| Field | Value |
|---|---|
| Vehicle VIN | VIN of the authorized Škoda |
| MyŠkoda API Key | API key created in MyŠkoda |
| Polling interval | 30 minutes initially |
| Read-only | Yes |
| Debug | No; enable for troubleshooting |

The API key is created and managed in the MyŠkoda application and is associated with the selected vehicle(s).

## API test

Before troubleshooting Domoticz, test the API directly:

```bash
curl \
  -H "X-API-Key: YOUR_API_KEY" \
  "https://public.api.connect.skoda-auto.cz/api/v1/vehicles/YOUR_VIN"
```

Never publish the API key, VIN, vehicle location, or an unredacted API response.

## Device definitions

`0.0.1-alpha` creates these stable Domoticz units:

| Unit | Name | Purpose |
|---:|---|---|
| 1 | Fuel level | Fuel percentage |
| 2 | Fuel range | Estimated combustion range |
| 3 | Odometer | Vehicle mileage |
| 4 | Doors locked | Lock state |
| 5 | Doors | Door state |
| 6 | Windows | Window state |
| 7 | Lights | Light state |
| 8 | Vehicle reachable | Connectivity/reachability |
| 9 | Vehicle in motion | Motion/parked state |
| 10 | Climate | Climate state when returned |
| 11 | Active ventilation | Ventilation state when returned |
| 12 | Parking position | Last parking coordinates/address |
| 13 | Last update | Last successful API update |
| 14 | API key expiry | API key expiry response header, when supplied |
| 15 | API status | API/rate-limit/partial-data status |

## Scope of 0.0.1-alpha

Implemented:

- API-key authentication
- VIN-based vehicle lookup
- vehicle-state polling
- stable Domoticz device creation
- fuel level/range
- odometer
- doors/windows/locks/lights
- vehicle reachability and motion
- climate and active ventilation when supplied by the API
- parking position
- API key expiry information
- rate-limit information
- API error/partial-data reporting

Not implemented:

- remote locking/unlocking
- climate/ventilation commands
- horn/flash
- charging commands
- MQTT event integration
- API-key renewal

Remote commands are intentionally disabled in this alpha. The first goal is to validate the actual response schema and capabilities of the Octavia 4.5 RS 265.

## Polling

The plugin defaults to a 30-minute poll. Do not use aggressive polling while testing. The API response rate-limit headers are exposed through the API status device/logging.

## Troubleshooting

### Plugin does not appear

Check:

```bash
ls -la /opt/domoticz/plugins/MySkodaAPI/
python3 -m py_compile /opt/domoticz/plugins/MySkodaAPI/plugin.py
```

Then restart Domoticz.

### 401

The API key is invalid or expired.

### 403

The API key is not authorized for the configured VIN or the requested access is not authorized.

### 422

The requested capability/operation is unavailable. This alpha performs read-only vehicle lookup.

### 429

A rate limit has been reached. Wait for the server-provided retry/reset interval and avoid tight polling.

## Development

The plugin follows the Domoticz Python plugin entry-point pattern: the XML plugin metadata is embedded in the module docstring, followed by `import Domoticz`, a `BasePlugin` implementation, and the global callbacks (`onStart`, `onStop`, `onHeartbeat`, `onCommand`). This is the pattern used by current Domoticz Python plugins. citeturn0search1turn0search4

## License

MIT. See `LICENSE`.
