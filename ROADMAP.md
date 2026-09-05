# Domoticz MySkoda API Integration — Roadmap

This document describes the planned development direction for the **Domoticz MySkoda API Integration** plugin.

The roadmap is intentionally flexible. Priorities may change depending on MySkoda API changes, Domoticz compatibility, user feedback, and the stability of the integration.

---

## Current Status

**Current release: `0.4.1` — First Stabilization Release**

The project has moved beyond the initial proof-of-concept stage and is now focused on reliability, API compatibility, maintainability, and expanding the amount of useful vehicle information exposed to Domoticz.

### Completed

* [x] Initial Domoticz plugin architecture
* [x] MySkoda API integration
* [x] Authentication handling
* [x] Vehicle discovery
* [x] Initial vehicle data integration
* [x] Domoticz device creation
* [x] Vehicle status information
* [x] Initial battery and range information
* [x] API key handling and configuration
* [x] Native API-key warning/status handling
* [x] Improved error handling
* [x] Improved logging and diagnostics
* [x] Long-running plugin architecture
* [x] Initial reliability improvements
* [x] Configuration and deployment documentation
* [x] Security documentation
* [x] Release/versioning structure
* [x] Intermediate development releases preserved in Git history
* [x] `v0.4.1` stabilization release

---

# Roadmap

## Phase 1 — Stabilization

**Status: 🟢 In progress**

The immediate priority is making the plugin reliable for continuous operation.

### Goals

* [ ] Improve handling of temporary MySkoda API failures
* [ ] Improve authentication/session recovery
* [ ] Handle expired or invalid credentials gracefully
* [ ] Prevent a temporary API failure from stopping the plugin
* [ ] Improve retry and back-off behaviour
* [ ] Detect and recover from incomplete API responses
* [ ] Improve timeout handling
* [ ] Improve handling of HTTP errors
* [ ] Improve handling of unexpected API responses
* [ ] Ensure Domoticz devices remain available when the API is temporarily unreachable
* [ ] Improve startup recovery after network outages
* [ ] Improve behaviour after Domoticz restarts
* [ ] Reduce unnecessary API requests
* [ ] Ensure the plugin can run continuously for extended periods

### Reliability principle

A temporary MySkoda service or network problem should result in a **temporary loss of updated data**, not a crashed or permanently broken Domoticz plugin.

---

# Phase 2 — MySkoda API Abstraction

**Status: 🟡 Planned**

Create a clean internal API layer so that MySkoda communication is separated from Domoticz device handling.

### Goals

* [ ] Separate API communication from Domoticz logic
* [ ] Centralize authentication
* [ ] Centralize API requests
* [ ] Centralize error handling
* [ ] Centralize retry logic
* [ ] Normalize API responses
* [ ] Provide consistent internal vehicle data structures
* [ ] Reduce duplicated API handling code
* [ ] Make future API changes easier to implement
* [ ] Make API behaviour easier to test independently

### Long-term objective

The Domoticz plugin should not need to know the details of every MySkoda API endpoint.

Instead:

```text
MySkoda API
     │
     ▼
API / Authentication Layer
     │
     ▼
Normalized Vehicle Data
     │
     ▼
Domoticz Integration Layer
     │
     ▼
Domoticz Devices
```

This separation should make the project easier to maintain when the upstream MySkoda API changes.

---

# Phase 3 — Expand Vehicle Data

**Status: 🟡 Planned**

Expose more useful information from MySkoda through Domoticz.

Potential data includes:

### Vehicle status

* [ ] Vehicle online/offline status
* [ ] Ignition status
* [ ] Driving status
* [ ] Vehicle state
* [ ] Current speed
* [ ] Odometer
* [ ] Trip information where available

### Battery

* [ ] State of charge
* [ ] Estimated electric range
* [ ] Charging state
* [ ] Charging power where available
* [ ] Charging progress
* [ ] Remaining charging time
* [ ] Target charge level
* [ ] Charging connection status
* [ ] Charging location where available

### Doors and locks

* [ ] Lock status
* [ ] Driver door
* [ ] Passenger door
* [ ] Rear doors
* [ ] Trunk/boot
* [ ] Hood/bonnet where available
* [ ] Window status where available

### Climate

* [ ] Climate status
* [ ] Cabin temperature where available
* [ ] Target temperature
* [ ] Climate running state
* [ ] Remote climate information
* [ ] Climate remaining time where available

### Vehicle location

* [ ] Latitude
* [ ] Longitude
* [ ] Location timestamp
* [ ] Location availability status

Location information will be handled carefully because it is sensitive vehicle data.

### Maintenance

* [ ] Service information
* [ ] Inspection information
* [ ] Remaining distance
* [ ] Remaining time
* [ ] Warning information where available

---

# Phase 4 — Domoticz Device Model

**Status: 🟡 Planned**

Improve how MySkoda information is represented inside Domoticz.

### Goals

* [ ] Consistent device naming
* [ ] Consistent device types
* [ ] Appropriate Domoticz units
* [ ] Improved device presentation
* [ ] Better grouping of vehicle devices
* [ ] Avoid unnecessary device creation
* [ ] Stable device identifiers
* [ ] Preserve devices across plugin restarts
* [ ] Handle newly discovered vehicle data without breaking existing devices

### Device categories

The long-term device structure is expected to be organized around categories such as:

```text
MySkoda
├── Vehicle
├── Battery
├── Charging
├── Doors & Locks
├── Climate
├── Location
├── Maintenance
└── Diagnostics
```

The exact Domoticz device types will depend on what Domoticz can represent cleanly.

---

# Phase 5 — Polling & API Efficiency

**Status: 🟡 Planned**

MySkoda data should be updated frequently enough to be useful without generating unnecessary API traffic.

### Goals

* [ ] Review default polling interval
* [ ] Make polling configurable
* [ ] Avoid duplicate requests
* [ ] Group compatible API requests
* [ ] Cache information where appropriate
* [ ] Avoid polling unchanged information unnecessarily
* [ ] Implement intelligent retry delays
* [ ] Handle API rate limits
* [ ] Detect temporary API throttling
* [ ] Avoid aggressive polling after failures

### Principle

The plugin should be a **good API citizen**.

Reliability must not be achieved by simply increasing the number of API requests.

---

# Phase 6 — Authentication & Security

**Status: 🟡 Ongoing**

Security remains a continuous development area.

### Goals

* [ ] Keep credentials out of logs
* [ ] Keep API keys out of logs
* [ ] Avoid exposing authentication tokens
* [ ] Improve secret handling
* [ ] Improve configuration validation
* [ ] Detect invalid authentication configuration
* [ ] Improve authentication failure messages
* [ ] Handle token/session expiration cleanly
* [ ] Review dependencies regularly
* [ ] Review security implications of new API functionality

### Sensitive data

The plugin may handle sensitive information including:

* MySkoda credentials
* API credentials/tokens
* Vehicle identifiers
* Vehicle location
* Vehicle status
* Charging information

Such information must never be unnecessarily written to logs, Git repositories, issue reports, or diagnostic output.

See [`SECURITY.md`](SECURITY.md) for the project's security policy.

---

# Phase 7 — Diagnostics & Logging

**Status: 🟡 Planned**

Make troubleshooting easier without exposing sensitive information.

### Goals

* [ ] Improve log levels
* [ ] Improve startup diagnostics
* [ ] Improve authentication diagnostics
* [ ] Improve API error diagnostics
* [ ] Improve vehicle discovery diagnostics
* [ ] Improve device creation diagnostics
* [ ] Clearly distinguish warnings from fatal errors
* [ ] Add useful recovery messages
* [ ] Make debug logging safe for sharing
* [ ] Avoid credentials and tokens in debug output

Potential logging levels:

```text
ERROR
WARNING
INFO
DEBUG
```

Debug logging should provide enough information to troubleshoot API problems without revealing secrets or unnecessary personal vehicle data.

---

# Phase 8 — Compatibility

**Status: 🟡 Planned**

Maintain compatibility with supported Domoticz and Python environments.

### Goals

* [ ] Test against current supported Domoticz releases
* [ ] Verify Python compatibility
* [ ] Avoid unnecessary third-party dependencies
* [ ] Detect unsupported environments cleanly
* [ ] Maintain compatibility with common Domoticz installation methods
* [ ] Test Docker-based deployments
* [ ] Test native Linux installations
* [ ] Test plugin upgrades

Compatibility should be considered whenever new functionality is introduced.

---

# Phase 9 — Testing

**Status: 🟡 Planned**

Introduce automated and repeatable testing.

### Goals

* [ ] Create API response fixtures
* [ ] Test authentication behaviour
* [ ] Test successful API responses
* [ ] Test malformed responses
* [ ] Test HTTP errors
* [ ] Test timeouts
* [ ] Test authentication failures
* [ ] Test retry behaviour
* [ ] Test vehicle discovery
* [ ] Test Domoticz device creation
* [ ] Test device updates
* [ ] Test plugin restart behaviour
* [ ] Test API changes using fixtures
* [ ] Add regression tests for fixed bugs

### Long-term goal

Core API and data-processing logic should be testable **without requiring a live vehicle or live MySkoda account**.

---

# Phase 10 — API Change Resilience

**Status: 🟡 Planned**

The MySkoda API is an external dependency and may change without notice.

The plugin should therefore be designed to tolerate upstream changes as gracefully as possible.

### Goals

* [ ] Detect unexpected API response structures
* [ ] Avoid crashes caused by missing fields
* [ ] Handle new fields safely
* [ ] Handle removed fields gracefully
* [ ] Log useful API compatibility warnings
* [ ] Keep API-specific code isolated
* [ ] Make endpoint changes easier to implement
* [ ] Maintain backward compatibility where practical

### Principle

An upstream API change should ideally result in:

```text
Warning
   ↓
Affected data unavailable
   ↓
Plugin continues running
```

rather than:

```text
API change
   ↓
Unhandled exception
   ↓
Plugin stops
```

---

# Phase 11 — User Experience

**Status: ⚪ Future**

Improve installation and everyday administration.

### Goals

* [ ] Simplify initial configuration
* [ ] Improve configuration descriptions
* [ ] Improve error messages in Domoticz
* [ ] Improve vehicle selection
* [ ] Improve configuration validation
* [ ] Improve upgrade instructions
* [ ] Improve troubleshooting documentation
* [ ] Provide clearer diagnostics for users
* [ ] Document common deployment scenarios

The goal is for the plugin to be usable by someone who does not need to understand the internals of the MySkoda API.

---

# Phase 12 — Production Stability

**Status: ⚪ Future**

Move from active development toward a stable production release.

### Goals

* [ ] Stable API abstraction
* [ ] Reliable authentication handling
* [ ] Robust error recovery
* [ ] Comprehensive vehicle data
* [ ] Stable Domoticz device model
* [ ] Automated regression testing
* [ ] Documented upgrade path
* [ ] Documented migration path
* [ ] Long-running stability testing
* [ ] Compatibility testing
* [ ] Security review
* [ ] Release process fully documented

### Target outcome

A stable release should be suitable for:

* 24/7 operation
* unattended operation
* automatic Domoticz restarts
* temporary network outages
* temporary MySkoda API outages
* long periods without manual intervention

---

# Release Strategy

The project uses incremental development releases.

The release history is intentionally preserved so that intermediate architecture and reliability work remains traceable.

Current development history includes:

```text
v0.0.1-beta
v0.0.2-alpha
v0.0.3-alpha
v0.0.3-alpha.1
v0.3.0-alpha4
v0.4.0-alpha3
v0.4.1
```

Future releases will continue to follow the project's development and stabilization needs rather than artificially forcing functionality into predefined versions.

---

# Development Priorities

When deciding what to implement next, the project prioritizes:

1. **Reliability**
2. **Security**
3. **API compatibility**
4. **Maintainability**
5. **Domoticz integration quality**
6. **API efficiency**
7. **Useful vehicle information**
8. **Testing**
9. **Documentation**
10. **Additional features**

A feature should not be added at the expense of long-term reliability or security.

---

# What Is Explicitly Not a Goal

The project does **not** aim to:

* Reimplement the MySkoda backend
* Circumvent MySkoda authentication
* Bypass API security mechanisms
* Generate unnecessary API traffic
* Store unnecessary personal or vehicle information
* Guarantee compatibility with undocumented upstream API behaviour
* Replace the official MySkoda application
* Provide safety-critical vehicle control

The plugin is intended primarily as a **read-oriented integration between MySkoda and Domoticz**, with functionality added only where it can be implemented reliably and responsibly.

---

# Long-Term Vision

The long-term vision is to provide a reliable bridge between MySkoda and Domoticz:

```text
                ┌──────────────────────┐
                │      MySkoda API     │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ Authentication & API │
                │       Layer          │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ Normalized Vehicle   │
                │        Data          │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ Domoticz Integration │
                │        Layer         │
                └──────────┬───────────┘
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
        ┌─────────┐   ┌─────────┐   ┌─────────┐
        │ Battery │   │ Vehicle │   │Charging │
        └─────────┘   └─────────┘   └─────────┘
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                     ┌───────────┐
                     │ Domoticz  │
                     └───────────┘
```

The ultimate objective is a plugin that can run continuously in a home-automation environment with minimal maintenance while remaining secure, efficient, and resilient to changes in the MySkoda API.

---

# Contributing

For Security-related issues, please follow the process described in [`SECURITY.md`](SECURITY.md).

---

# Disclaimer

This project is an independent community project and is not affiliated with, endorsed by, or sponsored by Škoda Auto or Volkswagen Group.

MySkoda API behaviour may change at any time. Features depending on undocumented or unofficial API behaviour may stop working without notice.

---

**Project:** Domoticz MySkoda API Integration
**Repository:** `janreimen/Domoticz-MySkodaAPI`
**Current release:** `0.4.1`

