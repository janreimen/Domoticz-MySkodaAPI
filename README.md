# MySkoda API Integration

A Domoticz Python plugin for the official Škoda MySkoda Public API.

This plugin communicates directly with the official MySkoda Public API and does
not use the deprecated `skodaconnect` / `myskoda` Python libraries.

## Status

**Version:** 0.0.1-beta

This is a beta release.

The current version is **read-only**. It retrieves vehicle information but does
not send commands to the vehicle.

## Features

The plugin currently retrieves:

- Vehicle name
- License plate
- Door lock status
- Door status
- Window status
- Lights
- Trunk
- Bonnet
- Sunroof
- Fuel level
- Fuel range
- Total vehicle range
- Odometer
- Parking state
- Parking address
- Parking GPS coordinates
- Air-conditioning state
- Target temperature
- Auxiliary heating state
- Active ventilation state
- Vehicle data timestamp
- API key expiration
- API rate-limit information
- API status

## Requirements

- Domoticz with Python plugin support
- Python 3
- A Škoda vehicle supported by the MySkoda Public API
- A MySkoda account
- A MySkoda Public API key
- The VIN of the vehicle

The plugin uses only Python standard-library modules.

No `pip install` is required.

## Installation

Clone the repository into the Domoticz plugins directory:

```bash
cd /opt/domoticz/plugins

git clone https://github.com/janreimen/Domoticz-MySkodaAPI.git MySkodaAPI

cd MySkodaAPI

chmod +x plugin.py

python3 -m py_compile plugin.py
