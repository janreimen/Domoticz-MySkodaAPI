# MySkoda API Integration

A Domoticz Python plugin for the official Škoda MySkoda Public API.

## Version

**0.0.2-alpha** — architecture/refactor release.

This release keeps the existing read-only behaviour while separating the Domoticz integration, API client, vehicle-state parser, device mapping, constants, and utility functions. Remote vehicle commands are **not** implemented yet.

## Architecture

```text
plugin.py
  ├── myskoda_api.py   API transport and HTTP/rate-limit metadata
  ├── vehicle.py       API response → normalized VehicleState
  ├── devices.py       VehicleState → Domoticz devices
  ├── constants.py     version, API configuration, units and selectors
  └── utils.py         safe conversion and formatting helpers
```

The architecture is deliberately kept dependency-free: only Python standard-library modules are used in addition to Domoticz's plugin API.

## Current features

The plugin retrieves the same read-only vehicle information as 0.0.1-beta:

- Vehicle name
- Door lock status
- Door/window status
- Lights
- Trunk, bonnet and sunroof
- Fuel level and range
- Total range
- Odometer
- Parking state/address/GPS
- Air-conditioning state and target temperature
- Auxiliary heating
- Active ventilation
- Vehicle data timestamp
- API key expiration
- API rate-limit information
- API status

## Installation

Clone into the Domoticz plugins directory:

```bash
cd /opt/domoticz/plugins
git clone https://github.com/janreimen/Domoticz-MySkodaAPI.git MySkodaAPI
cd MySkodaAPI
chmod +x plugin.py
python3 -m py_compile plugin.py constants.py utils.py vehicle.py myskoda_api.py devices.py
```

Restart Domoticz and add **MySkoda API Integration** as hardware.

- **Vehicle VIN** → Username field
- **MyŠkoda API Key** → Password field
- Poll interval → 15, 30 or 60 minutes
- Debug → Normal or Debug

## Important

0.0.2-alpha is an architecture release. Existing unit numbers are retained so an upgrade does not intentionally renumber the current devices.

Remote commands are still disabled. Clicking a selector does not send a command to the vehicle.

## Development direction

Future releases can add persistent state/cache, smarter rate-limit-aware scheduling, battery/charging telemetry and verified remote commands without putting those responsibilities back into `plugin.py`.
