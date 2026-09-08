# Roadmap

The roadmap below describes the intended direction of the project. Features marked as planned are not considered implemented until they appear in a released version.

---

## [0.4.2] — Stabilisation / Maintenance

### Planned

The immediate priority after `0.4.1` is to harden the existing device lifecycle.

### Focus

* Fix Domoticz device-type migration crashes.
* Make device characteristic changes safe.
* Improve upgrade handling.
* Ensure existing IDX/unit assignments remain stable.
* Improve provisioning idempotency.
* Ensure an existing device is reused instead of creating duplicates.
* Improve error handling around Domoticz device updates.
* Verify clean installation and upgrade paths.

### Goal

> An existing `0.4.1` installation must be upgradeable without manual device repair.

---

# [0.5.x] — Complete Read-Only Integration

## Goal

Complete the **read-only vehicle model** before introducing remote commands.

The planned vehicle model is:

```text
Vehicle
├── Status
├── Battery
├── Range
├── Fuel
├── Charging
├── Doors
├── Windows
├── Lights
├── Climate
├── Parking
├── Location
└── Diagnostics
```

### Vehicle

Potential additions/refinements:

* complete vehicle status
* connectivity state
* last communication
* telemetry age
* vehicle capabilities
* supported operations

### Battery

* battery state of charge
* electric range
* battery-related status
* target state of charge where available

### Fuel

* fuel level
* fuel range
* total range
* engine/fuel type

### Charging

* charging state
* charging connection
* target state of charge
* charge mode
* charging-related timestamps

### Doors / Body

* lock state
* door states
* windows
* trunk
* bonnet
* sunroof where available

### Lights

* exterior light state
* relevant light states exposed by the API

### Climate

* climate state
* target temperature
* auxiliary heating
* ventilation where supported

### Parking / Location

* parking state
* GPS position where available
* address where available
* last known position

### Diagnostics

* API status
* HTTP status
* MyŠkoda problem type
* API key status
* API rate remaining
* API rate reset
* vehicle capture age
* partial-data warnings

### Principle

> `0.5.x` should answer the question:
> **"Can Domoticz reliably show everything useful that MyŠkoda exposes without controlling the vehicle?"**

---

# [0.6.x] — Remote Commands

## Goal

Introduce controlled, verified write operations.

Initial planned commands:

* Lock vehicle
* Unlock vehicle
* Start climate
* Stop climate
* Start charging
* Stop charging

### Command architecture

Every command should follow:

```text
Domoticz action
      │
      ▼
Capability check
      │
      ▼
Command validation
      │
      ▼
MyŠkoda API
      │
      ▼
Command result
      │
      ▼
Vehicle state refresh
      │
      ▼
Domoticz update
```

### Safety requirements

* Do not expose commands unsupported by the vehicle.
* Do not treat a successful HTTP request as proof that the vehicle executed the command.
* Verify command results where the API allows it.
* Refresh vehicle state after commands.
* Clearly expose command failures.
* Prevent accidental repeated commands where appropriate.
* Preserve read-only functionality if command support becomes temporarily unavailable.

### Principle

> **A command is not successful until its result can be verified.**

---

# [0.7.x] — Automation & Advanced Vehicle Features

This milestone is intentionally less prescriptive.

Potential features include:

### Notifications

* vehicle unlocked
* charging stopped
* charging failed
* API key approaching expiration
* vehicle unavailable
* stale vehicle data
* maintenance approaching

### Domoticz automation

Potential triggers for:

* vehicle arrival
* vehicle departure
* charging state changes
* low battery
* low fuel
* vehicle lock state
* climate state

### Smart charging

Potential future functionality:

* charging target
* controlled start/stop
* charging schedules
* automation based on electricity availability

All such functionality depends on what the MyŠkoda API reliably supports.

---

# [0.8.x] — Advanced Integration

Potential areas:

## Multi-vehicle support

Move from a single vehicle model toward:

```text
MyŠkoda Account
├── Vehicle A
├── Vehicle B
└── Vehicle C
```

The architecture should allow multiple vehicles without duplicating the plugin implementation.

## Maintenance

Potential maintenance model:

```text
Maintenance
├── Inspection
├── Service
├── Oil
├── Brakes
├── Other
└── Next Service
```

Possible values:

* due date
* days remaining
* distance remaining
* due state

## Historical information

Where the API provides suitable information:

* charging history
* trip information
* distance history
* consumption information
* additional vehicle statistics

---

# [0.9.x] — Release Candidate

## Feature Freeze

`0.9.x` should be the final stabilization phase before `1.0.0`.

### No major new features

Focus on:

* API compatibility
* Domoticz compatibility
* device migration
* device provisioning
* command reliability
* error handling
* performance
* logging
* testing
* documentation

### Testing

The project should have automated tests for:

* API response parsing
* vehicle-state normalization
* partial API responses
* error responses
* rate limiting
* retry handling
* device provisioning
* existing-device reuse
* device migration
* command handling
* command verification

### Compatibility testing

Test at minimum:

```text
Fresh installation
Existing installation
Upgrade from previous version
Device characteristic migration
API failure
Authentication failure
Rate limiting
Vehicle unavailable
Partial API response
```

### Goal

> `0.9.x` should be boring.

If a new installation and an existing installation both behave predictably for a long period, the project is ready for 1.0.

---

# [1.0.0] — Production Stable

## Definition

`1.0.0` will represent the first production-stable release of Domoticz-MySkodaAPI.

### API

* Stable authentication
* Reliable polling
* Retry handling
* Rate-limit handling
* Error classification
* Graceful degradation
* Stale-data handling

### Vehicle

* Complete supported telemetry
* Stable normalized vehicle model
* Battery
* Range
* Fuel
* Charging
* Doors
* Windows
* Lights
* Climate
* Parking
* Location
* Diagnostics

### Commands

* Supported remote commands
* Capability detection
* Command verification
* Safe failure handling

### Domoticz

* Stable device model
* Stable IDX/unit assignments
* Safe provisioning
* Safe upgrades
* Device migration
* No duplicate devices
* Correct native Domoticz device types

### Architecture

* API layer
* normalized vehicle-state layer
* provisioning/device layer
* Domoticz client layer
* command layer
* configuration layer

### Documentation

* Installation
* Configuration
* API requirements
* Device list
* Device/unit mapping
* Remote commands
* Troubleshooting
* Upgrade instructions
* Security
* Changelog
* Roadmap

### Principle

> **1.0.0 is not defined by the number of sensors. It is defined by reliability, compatibility and predictable behaviour.**

---

# Post-1.0 Development

After `1.0.0`, development should focus on extending functionality without breaking existing installations.

Potential `1.x` features include:

### Energy & Charging

* charging history
* charging energy
* consumption statistics
* charging cost estimation
* charging analytics

### Trips

Where supported by the API:

* trip history
* trip distance
* trip consumption
* trip statistics

### Location

* geofencing
* home/work detection
* arrival/departure events
* location-based automation

### Automation

* advanced charging automation
* climate automation
* vehicle arrival/departure automation
* notification rules

### Vehicle Support

Expand compatibility with additional Škoda vehicles as their MyŠkoda API representations become available.

---

# Development Principles

The following principles should remain valid throughout the project.

## 1. Preserve existing Domoticz devices

Existing unit/IDX assignments should be treated as stable API contracts.

## 2. Never create duplicate devices unnecessarily

Provisioning must be idempotent.

## 3. API failures must not destroy good data

Temporary API failures should preserve the last known valid vehicle state where appropriate.

## 4. Read and write operations must remain clearly separated

Telemetry and remote commands should never be mixed accidentally.

## 5. Commands must be verified

A successful HTTP response is not automatically proof of vehicle execution.

## 6. Use native Domoticz device types where possible

The plugin should integrate naturally into Domoticz rather than exposing raw API structures.

## 7. Do not expose every API field automatically

Only useful, stable and semantically meaningful values should become Domoticz devices.

## 8. API changes must be expected

The MyŠkoda API may evolve. Parsing and normalization should therefore be tolerant of optional and partial data.

## 9. Standard library first

Avoid unnecessary third-party dependencies unless they provide substantial value.

## 10. Stability before features

Especially approaching `1.0.0`, reliability and upgrade safety take priority over adding additional telemetry.

---

# Version Strategy

```text
0.4.x
  │
  ├── Stabilize current beta
  │
  ▼
0.5.x
  │
  ├── Complete read-only integration
  │
  ▼
0.6.x
  │
  ├── Remote commands
  │
  ▼
0.7.x
  │
  ├── Automation / advanced features
  │
  ▼
0.8.x
  │
  ├── Multi-vehicle / maintenance / history
  │
  ▼
0.9.x
  │
  ├── Feature freeze
  ├── Testing
  ├── Compatibility
  └── Release candidate
  │
  ▼
1.0.0
  │
  └── Production stable
  │
  ▼
1.x
     └── New capabilities without breaking existing installations
```

---

# Status Legend

* **Released** — implemented in a published version.
* **Planned** — explicitly targeted for a future release.
* **Potential** — technically interesting future functionality, subject to API capabilities and project priorities.
* **Not implemented** — not currently available.

---

# Current Project Direction

The overall evolution of Domoticz-MySkodaAPI is:

```text
Experimental API integration
        ↓
Structured API client
        ↓
Normalized vehicle model
        ↓
Reliable telemetry
        ↓
Native Domoticz devices
        ↓
Stable Beta
        ↓
Complete read-only integration
        ↓
Verified remote commands
        ↓
Advanced automation
        ↓
Release Candidate
        ↓
Production Stable 1.0
```

The central goal is to build a **reliable, maintainable and upgrade-safe bridge between the MyŠkoda API and Domoticz**, rather than simply exposing as many API fields as possible.

