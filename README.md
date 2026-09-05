# Domoticz MySkoda API Integration

A Domoticz Python plugin for integrating **Škoda vehicles through the MySkoda API** into Domoticz.

**Current release:** `0.4.1`

---

## ⚠️ Project Status

This project is under active development.

Version `0.4.1` represents the current development/release baseline and may still evolve as the MySkoda API changes.

The plugin depends on services operated by Škoda and therefore functionality may change without notice if the upstream API changes.

---

## Roadmap

The goal of **Domoticz MySkoda API Integration** is to provide a reliable, maintainable and feature-complete MySkoda integration for Domoticz.

Development is planned in incremental releases, with each release improving the plugin's architecture, reliability, vehicle data coverage and usability.

### Completed / Current

* [x] Initial Domoticz plugin architecture
* [x] MySkoda API integration
* [x] Authentication handling
* [x] Vehicle discovery
* [x] Initial vehicle data integration
* [x] Domoticz device creation
* [x] Improved error handling and logging
* [x] Configuration and deployment documentation
* [x] Security documentation
* [x] Release `0.4.1`

### Next Development Steps

* [ ] Further improve API reliability and error handling
* [ ] Improve authentication/session handling
* [ ] Expand vehicle data coverage
* [ ] Improve charging information and status handling
* [ ] Improve vehicle state and lock/door information
* [ ] Improve Domoticz device naming and presentation
* [ ] Reduce unnecessary API requests and improve polling efficiency
* [ ] Improve recovery from temporary MySkoda API failures
* [ ] Improve diagnostics and logging
* [ ] Add regression testing for API responses and vehicle data
* [ ] Improve compatibility across supported Škoda models

### Longer-Term Goals

* [ ] Stable and maintainable API abstraction
* [ ] Comprehensive coverage of available MySkoda vehicle data
* [ ] Reliable long-running operation in Domoticz
* [ ] Robust handling of upstream MySkoda API changes
* [ ] Comprehensive automated testing
* [ ] Production-ready stable release
* [ ] Clear upgrade and migration path between releases

### Development Philosophy

The project prioritizes:

1. **Reliability** — the plugin should continue operating despite temporary API failures.
2. **Security** — credentials and authentication data must be handled safely.
3. **Maintainability** — the codebase should remain understandable and modular.
4. **Compatibility** — support should be extended across different Škoda vehicles where the API permits it.
5. **Responsible API usage** — requests should be minimized and polling should respect the upstream service.
6. **Domoticz integration quality** — vehicle information should be exposed as useful, predictable Domoticz devices.

The roadmap is intentionally iterative. MySkoda API behaviour can change independently of this project, so individual features may be reprioritized as the upstream service evolves.

---

## Features

The plugin connects Domoticz to the MySkoda service and exposes available vehicle information as Domoticz devices.

Depending on the vehicle and the information exposed by the MySkoda API, the plugin can provide:

* Vehicle status
* Battery state of charge
* Electric driving range
* Charging status
* Charging information
* Vehicle mileage
* Lock status
* Door status
* Climate information
* Vehicle location
* Service information
* Other vehicle data provided by the API

The exact devices available depend on the vehicle, its equipment, the MySkoda account, and the current API implementation.

---

## Supported Vehicles

The plugin is intended for Škoda vehicles supported by the MySkoda platform.

Support is not necessarily identical across all models.

A particular value or function may be unavailable because:

* The vehicle does not support it.
* The vehicle configuration does not provide it.
* MySkoda does not expose it for that vehicle.
* The upstream API has changed.
* The functionality is not yet implemented by this plugin.

---

## Requirements

### Domoticz

A working Domoticz installation with Python plugin support is required.

### Python

Python 3 is required.

Check your Python installation:

```bash
python3 --version
```

### MySkoda Account

You need a valid MySkoda account with at least one associated vehicle.

### Network Connectivity

The Domoticz host must have outbound Internet access to communicate with the MySkoda services.

---

## Installation

Clone the repository into the Domoticz plugins directory.

For example:

```bash
cd /opt/domoticz/plugins
git clone https://github.com/janreimen/Domoticz-MySkodaAPI.git MySkodaAPI
```

The plugin directory should contain:

```text
plugins/
└── MySkodaAPI/
    ├── plugin.py
    ├── README.md
    ├── DEPLOY.md
    ├── SECURITY.md
    ├── LICENSE
    └── ...
```

Restart Domoticz after installation.

For detailed deployment instructions, see:

**[DEPLOY.md](DEPLOY.md)**

---

## Configuration

After installing the plugin:

1. Open the Domoticz web interface.
2. Go to **Setup → Hardware**.
3. Add a new hardware device.
4. Select **MySkoda API Integration**.
5. Enter the required configuration.
6. Save the hardware configuration.
7. Restart Domoticz if required.

The plugin will authenticate against MySkoda and retrieve the vehicle information available to the configured account.

---

## Authentication

The plugin requires authentication against the MySkoda service.

Credentials are sensitive and must be protected.

**Never commit MySkoda credentials, access tokens, refresh tokens, cookies, or other authentication data to Git.**

Do not publish credentials in:

* GitHub Issues
* GitHub Discussions
* Pull Requests
* Screenshots
* Domoticz logs
* Configuration files committed to the repository

See **[SECURITY.md](SECURITY.md)** for the security policy.

---

## Domoticz Devices

The plugin creates Domoticz devices based on the vehicle data returned by the MySkoda API.

Depending on the vehicle and API capabilities, devices may cover areas such as:

| Category | Possible information           |
| -------- | ------------------------------ |
| Vehicle  | Status, mileage                |
| Battery  | State of charge, range         |
| Charging | Charging state and information |
| Locks    | Lock state                     |
| Doors    | Door state                     |
| Climate  | Climate state                  |
| Location | Vehicle position               |
| Service  | Service information            |

The actual device list is determined by the information available from the API.

---

## API Behaviour

This plugin communicates with external MySkoda services.

The upstream API is not controlled by this project and may change independently.

Changes can affect:

* Authentication
* API endpoints
* Request formats
* Response formats
* Available vehicle information
* Vehicle commands
* Rate limits
* Service availability

If the MySkoda service changes, an update to this plugin may be required.

---

## Polling

The plugin periodically communicates with the MySkoda API to update Domoticz.

Polling should be performed responsibly.

Excessive polling can result in:

* API rate limiting
* Temporary API failures
* Increased network traffic
* Unnecessary load on the upstream service

Do not configure unnecessarily aggressive polling intervals.

---

## Troubleshooting

Check the Domoticz log for plugin-related messages.

Useful log entries may contain:

```text
MySkoda
Traceback
ImportError
ModuleNotFoundError
Authentication
HTTP
API
```

You can also verify that the plugin has no Python syntax errors:

```bash
python3 -m py_compile /opt/domoticz/plugins/MySkodaAPI/plugin.py
```

A successful syntax check produces no output.

For deployment and troubleshooting information, see:

**[DEPLOY.md](DEPLOY.md)**

---

## Updating

It is recommended to deploy tagged releases rather than arbitrary development commits.

Example:

```bash
cd /opt/domoticz/plugins/MySkodaAPI
git fetch --tags
git checkout 0.4.1
```

Then restart Domoticz:

```bash
sudo systemctl restart domoticz
```

For Docker installations:

```bash
docker restart domoticz
```

Replace the container name if your Domoticz container uses a different name.

---

## Rollback

If a release causes problems, you can return to a previous tagged release.

For example:

```bash
cd /opt/domoticz/plugins/MySkodaAPI
git fetch --tags
git checkout <PREVIOUS_VERSION>
```

Restart Domoticz afterwards.

Always check the Domoticz log after a rollback.

---

## Docker

The plugin can be used with a Docker-based Domoticz installation provided that the plugin is available inside the Domoticz container.

A persistent Domoticz volume should normally be used so that the plugin survives container recreation.

After installing or updating the plugin:

```bash
docker restart domoticz
```

The exact paths depend on the Domoticz Docker image and volume configuration.

---

## Security

Security is particularly important because the plugin interacts with a connected vehicle service.

Please read:

**[SECURITY.md](SECURITY.md)**

Never publish:

* MySkoda passwords
* Access tokens
* Refresh tokens
* Session cookies
* Authorization headers
* VINs
* Vehicle location data
* Other sensitive vehicle information

When sharing logs, redact sensitive information first.

---

## Development

The repository is developed using Git.

Clone the repository:

```bash
git clone https://github.com/janreimen/Domoticz-MySkodaAPI.git
```

Create a development branch rather than working directly on the release branch:

```bash
git checkout -b feature/my-change
```

Before committing changes, verify:

```bash
git status
git diff
```

Check Python syntax:

```bash
python3 -m py_compile plugin.py
```

Do not commit credentials or other secrets.

---

## Release Versioning

The project uses version numbers to identify releases.

The version implemented by the plugin should correspond to the repository release being deployed.

For example:

```text
0.0.1-alpha
0.0.2-alpha
...
0.4.1
```

When preparing releases, create and commit the required intermediate release before moving to the next target release.

This keeps Git history, release tags, and the version reported by the plugin consistent.

---

## Disclaimer

This project is an independent community project.

It is not affiliated with, endorsed by, or sponsored by Škoda Auto unless explicitly stated otherwise.

MySkoda is a service operated by Škoda. The availability and behaviour of the service and its APIs are outside the control of this project.

Use of the plugin is at your own risk.

---

## License

This project is distributed under the license included in:

**[LICENSE](LICENSE)**

---

## Repository

Source code and releases:

**https://github.com/janreimen/Domoticz-MySkodaAPI**

For deployment instructions:

**[DEPLOY.md](DEPLOY.md)**

For security issues:

**[SECURITY.md](SECURITY.md)**

