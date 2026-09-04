# Changelog

## 0.0.2-alpha - Architecture/refactor

- Split the 0.0.1-beta monolithic plugin into dedicated modules.
- Added `MySkodaAPI` HTTP client and `APIResult` response model.
- Added normalized `VehicleState` parsing layer.
- Added `DeviceManager` for Domoticz device creation/update logic.
- Centralized version, API, unit and selector constants.
- Preserved existing Domoticz unit numbers 1-23.
- Preserved read-only behaviour; no vehicle commands were added.
- Made GPS parsing defensive against malformed coordinates.
- Kept API key out of debug output.
- Added compile/test scaffolding for future releases.

### 0.0.2-alpha hotfix
- Fixed `DeviceManager` access to Domoticz `Devices`; the refactored module no longer assumes `Devices` is a global in `devices.py`.
- Existing Domoticz hardware/devices remain compatible; no reintegration is required.
