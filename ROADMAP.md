# Roadmap

The roadmap describes the intended future development of **Domoticz-MySkodaAPI**.

The project is currently at **0.4.1 — First Stable Beta**.

The roadmap deliberately separates:

* **Planned** — intended development target.
* **Potential** — useful future functionality, but not yet committed.
* **API-dependent** — dependent on capabilities exposed by the MyŠkoda Public API.
* **Deferred** — deliberately postponed until the architecture or API is ready.

Features are **not considered implemented** until they are released in a version of the plugin.

---

# Current State — 0.4.1

## 0.4.1 — First Stable Beta

The current release provides a mature **read-only** MyŠkoda integration for Domoticz.

The current implementation includes:

* MyŠkoda Public API integration.
* `X-API-Key` authentication.
* VIN-based vehicle identification.
* HTTP 429 handling.
* transient HTTP 5xx handling.
* `Retry-After` handling.
* bounded exponential backoff.
* last-known-good vehicle state.
* partial API response handling.
* API rate-limit information.
* API-key expiry information.
* API-key health status.
* API problem/status reporting.
* vehicle telemetry.
* fuel information.
* range information.
* odometer information.
* daily and previous-day distance.
* battery state of charge.
* electric range.
* charging state.
* charging connection.
* charge target.
* charge mode.
* climate information.
* security information.
* doors, windows and body-state information.
* parking information.
* GPS/location information.
* telemetry timestamps.
* API capabilities.
* supported operations.
* native Domoticz device types.
* stable Domoticz unit assignments.
* local runtime state for persistent calculations.

The established Domoticz device model currently uses units **1–44**.

The integration remains intentionally **read-only**. Selector devices are telemetry displays and do not issue vehicle commands.

---

# Immediate Priority

## 0.4.2 — Stabilisation

### Status

**Planned**

### Objective

Harden the existing 0.4.x architecture before introducing new functionality.

The immediate priority is the Domoticz device lifecycle.

GitHub issue #6 currently documents a problem where changing device characteristics during an upgrade can cause the plugin to crash. This needs to be resolved before the device model can be considered sufficiently stable for further expansion.

### Work

* Fix device-type migration crashes.
* Make Domoticz device characteristic changes safe.
* Improve device provisioning.
* Make provisioning fully idempotent.
* Reuse existing devices whenever possible.
* Prevent accidental duplicate devices.
* Preserve established unit/IDX assignments.
* Improve device-update error handling.
* Safely migrate existing installations.
* Verify fresh installation behaviour.
* Verify upgrade behaviour.
* Verify recovery after interrupted provisioning.
* Verify behaviour when a device has been manually modified in Domoticz.

### Acceptance criteria

A `0.4.1` installation should be upgradeable without:

* manually deleting devices,
* manually recreating devices,
* losing established unit assignments,
* creating duplicate devices,
* or crashing the plugin.

### Principle

> **Before adding more devices, make the existing device model bulletproof.**

---

# 0.5.x — Complete Read-Only Integration

## Status

**Planned**

GitHub issue #3 defines `0.5.0` as the **complete read-only implementation**.

The purpose of this milestone is to finish the vehicle information model before introducing remote commands.

## Goal

> Domoticz should expose everything useful and reliably available from the MyŠkoda API without controlling the vehicle.

---

## Vehicle

### Planned

Complete and normalize:

* vehicle state.
* connectivity state.
* last communication.
* telemetry capture age.
* vehicle capabilities.
* supported operations.
* vehicle identification.
* API-provided vehicle metadata where useful.

---

## Battery

### Planned

* Battery state of charge.
* Electric range.
* Battery state.
* Target state of charge where available.
* Battery-related timestamps where useful.

---

## Fuel

### Planned

* Fuel level.
* Fuel range.
* Total range.
* Engine/fuel type.
* Fuel telemetry timestamp.

---

## Charging

### Planned

* Charging state.
* Charging connection.
* Charge target.
* Charge mode.
* Charging capture timestamp.
* Additional charging information exposed by the API.

---

## Doors and Body

### Planned / completion

Ensure consistent representation of:

* Lock state.
* Doors.
* Windows.
* Trunk.
* Bonnet.
* Sunroof where available.

---

## Lights

### Planned / completion

Expose useful light-state information available from the API.

Only stable and meaningful states should become Domoticz devices.

---

## Climate

### Planned / completion

* Climate state.
* Target temperature.
* Auxiliary heating.
* Active ventilation.
* Additional climate telemetry where supported.

The integration remains read-only during this milestone.

---

## Parking and Location

### Planned / completion

* Parking state.
* Parking address.
* GPS position.
* Last known position.
* Location timestamp where available.

---

## Diagnostics

### Planned / completion

Continue improving:

* API status.
* HTTP status.
* API problem type.
* API-key status.
* API-key expiry.
* Rate-limit information.
* Rate-limit remaining.
* Rate-limit reset.
* Vehicle capture age.
* Partial API-data errors.
* Data quality.

---

## Device Model

The existing unit assignments must remain stable.

New devices must:

1. use the correct native Domoticz device type;
2. have a meaningful name;
3. use correct units;
4. be provisioned idempotently;
5. support migration;
6. never unnecessarily replace an existing device.

### Principle

> **The Domoticz device model is an interface contract.**

Once a unit/IDX has been released, changing its meaning should be treated as a breaking change.

---

# 0.5.x — Architecture Hardening

While completing the read-only model, the internal architecture should continue moving toward clearly separated responsibilities.

Target architecture:

```text
MyŠkoda API
     │
     ▼
API Client
     │
     ▼
Vehicle Response
     │
     ▼
Normalization
     │
     ▼
Vehicle State / Snapshot
     │
     ├──────────────┐
     ▼              ▼
Provisioning     Diagnostics
     │
     ▼
Domoticz
```

The goal is to avoid coupling raw API structures directly to Domoticz devices.

This will make future API changes easier to handle.

---

# 0.6.x — Remote Commands

## Status

**Planned**

GitHub issue #4 defines the next major functional step as remote commands.

This is the point where the plugin changes from:

```text
MyŠkoda API
      ↓
Domoticz
```

to:

```text
MyŠkoda API
      ↕
Domoticz
```

## Initial command set

### Vehicle

* Lock.
* Unlock.

### Climate

* Start climate.
* Stop climate.

### Charging

* Start charging.
* Stop charging.

Additional commands should only be introduced when their API behaviour is well understood.

---

# Command Architecture

Commands must never be implemented as a simple:

```text
Domoticz click
    ↓
HTTP request
```

Instead:

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
Safety checks
      │
      ▼
MyŠkoda API
      │
      ▼
API response
      │
      ▼
Verification
      │
      ▼
Vehicle state refresh
      │
      ▼
Domoticz update
```

## Safety requirements

* Do not expose unsupported commands.
* Do not assume every vehicle supports every operation.
* Validate command availability before sending.
* Handle API failures explicitly.
* Handle rate limits.
* Prevent uncontrolled command repetition.
* Refresh vehicle state after a command.
* Verify command execution where the API allows it.
* Clearly report unsuccessful commands.
* Never silently convert a failed command into a successful Domoticz state.

### Principle

> **A successful HTTP request is not necessarily a successful vehicle command.**

---

# 0.7.x — Advanced Vehicle Features

## Status

**Potential / Planned**

After remote commands are stable, the integration can start making more use of Domoticz automation.

Potential areas include:

## Notifications

Potential notifications:

* vehicle unlocked.
* charging stopped.
* charging failed.
* vehicle unavailable.
* stale vehicle data.
* API key approaching expiration.
* API key expired.
* maintenance approaching.
* low battery.
* low fuel.

These should preferably be exposed through Domoticz states/events rather than requiring a separate notification framework.

---

## Automation

Potential automation triggers:

* vehicle arrival.
* vehicle departure.
* charging started.
* charging stopped.
* low battery.
* low fuel.
* vehicle locked/unlocked.
* climate started/stopped.
* vehicle becomes unavailable.

---

## Smart Charging

### Potential

If reliably supported by the API:

* charging target.
* controlled start/stop.
* charging schedules.
* charging based on household conditions.
* charging based on electricity availability.
* charging based on battery level.

This area is explicitly **API-dependent**.

The plugin should not attempt to emulate functionality that the API does not safely support.

---

# 0.8.x — Advanced Integration

## Status

**Potential / Planned**

This milestone is intentionally flexible.

The exact contents should depend on the capabilities discovered while implementing 0.5–0.7.

---

# Multi-Vehicle Support

### Potential

Move from a single configured vehicle toward:

```text
MyŠkoda Account
│
├── Vehicle A
│   ├── Status
│   ├── Battery
│   ├── Charging
│   ├── Climate
│   └── Maintenance
│
├── Vehicle B
│   └── ...
│
└── Vehicle C
    └── ...
```

The architecture should allow multiple vehicles without duplicating the complete plugin implementation.

### Important

Multi-vehicle support should be introduced only after the single-vehicle device/provisioning model is stable.

---

# Maintenance

## Status

**Planned / API-dependent**

A structured maintenance subsystem should be introduced when the MyŠkoda API exposes sufficiently reliable maintenance information.

Potential structure:

```text
Maintenance
├── Inspection
├── Service
├── Oil
├── Brakes
├── Other
└── Next Service
```

Potential values:

* due date.
* days remaining.
* distance remaining.
* due state.
* service type.
* maintenance status.

### Design goal

Maintenance information should use correct native Domoticz sensor representations rather than arbitrary text or generic counters.

---

# Historical Data

## Status

**Potential / API-dependent**

Where the API provides suitable data:

* charging history.
* trip information.
* trip distance.
* consumption.
* vehicle statistics.
* additional distance information.

The plugin should distinguish between:

1. data supplied directly by MyŠkoda;
2. locally calculated values;
3. locally persisted history.

This distinction is important for data quality and troubleshooting.

---

# 0.8.x — Data Quality and Historical Intelligence

Potential future improvements include:

* better stale-data detection.
* telemetry age.
* state-change detection.
* historical trend calculation.
* charging-session detection.
* distance statistics.
* consumption statistics.

Local calculations must never be confused with values directly reported by the API.

---

# 0.9.x — Release Candidate

## Status

**Planned**

`0.9.x` should be the final stabilization phase before `1.0.0`.

## Feature Freeze

No major new functionality should be introduced during the release-candidate phase.

Focus moves to:

* reliability.
* compatibility.
* upgrade safety.
* migration.
* performance.
* testing.
* logging.
* documentation.
* security.

---

# Automated Testing

Before `1.0.0`, the project should have automated coverage for:

### API

* normal responses.
* partial responses.
* malformed responses.
* HTTP 429.
* HTTP 5xx.
* authentication errors.
* API problem types.
* rate-limit headers.
* API-key expiry.
* missing optional fields.

### Vehicle normalization

* battery.
* charging.
* fuel.
* range.
* climate.
* security.
* location.
* timestamps.
* missing data.

### Domoticz provisioning

* fresh installation.
* existing installation.
* device reuse.
* duplicate prevention.
* device migration.
* changed device characteristics.
* upgrade from previous versions.
* interrupted provisioning.

### Commands

* capability detection.
* validation.
* successful command.
* failed command.
* timeout.
* rate limiting.
* verification.
* state refresh.

---

# Compatibility Testing

Before `1.0.0`, at minimum test:

```text
Fresh installation
Existing installation
Upgrade from previous version
Device characteristic migration
Existing IDX reuse
API failure
Authentication failure
Rate limiting
Vehicle unavailable
Partial API response
Missing optional API fields
Command failure
Command verification
```

The goal is that both:

```text
Fresh installation
```

and:

```text
Long-running installation upgraded through multiple releases
```

behave predictably.

---

# 0.9.x — Documentation Freeze

Before 1.0:

* README must describe the actual current feature set.
* CHANGELOG must contain the complete release history.
* ROADMAP must describe future development.
* SECURITY.md must be current.
* Device/unit mapping must be documented.
* Configuration options must be documented.
* Remote commands must be documented.
* Upgrade procedures must be documented.
* Known limitations must be documented.

Documentation must describe released behaviour, not planned behaviour as if it already existed.

---

# 1.0.0 — Production Stable

## Status

**Long-term target**

`1.0.0` represents the first production-stable release.

It is not defined by the number of Domoticz devices.

It is defined by:

> **Reliability, compatibility, predictable behaviour and safe upgrades.**

---

## API

1.0 should provide:

* stable authentication.
* reliable polling.
* bounded retries.
* rate-limit handling.
* API error classification.
* graceful degradation.
* stale-data handling.
* partial-response handling.

---

## Vehicle

1.0 should provide the complete supported telemetry model:

* vehicle state.
* battery.
* range.
* fuel.
* charging.
* doors.
* windows.
* lights.
* climate.
* parking.
* location.
* diagnostics.
* maintenance where reliably available.

---

## Commands

1.0 should provide only commands that are:

* supported by the API;
* supported by the vehicle;
* safely validated;
* properly handled on failure;
* verified where possible.

---

## Domoticz

1.0 should guarantee:

* stable device model.
* stable unit/IDX assignments.
* idempotent provisioning.
* safe upgrades.
* safe migration.
* no unnecessary duplicate devices.
* correct native Domoticz device types.
* predictable state updates.

---

## Architecture

The architecture should have clearly separated:

```text
API Client
     │
     ▼
Vehicle Data / Normalization
     │
     ▼
Vehicle State / Snapshot
     │
     ├── Diagnostics
     │
     ├── Commands
     │
     └── Provisioning
              │
              ▼
           Domoticz
```

---

# 1.0.0 Compatibility Contract

After 1.0.0, the following should be treated as compatibility-sensitive:

### Domoticz device units

Existing unit assignments should not be casually changed.

### Device meaning

Changing what an existing unit represents should be treated as a breaking change.

### Configuration

Existing configuration should remain valid wherever possible.

### API behaviour

API changes should be isolated behind the API/normalization layer.

### Runtime state

Changes to local state files should include migration or compatibility handling when required.

---

# Post-1.0 — 1.x Development

## Principle

After `1.0.0`, new functionality should be added **without breaking existing installations**.

Potential 1.x development includes:

---

## Energy & Charging

Potential:

* charging history.
* charging energy.
* consumption statistics.
* charging cost estimation.
* charging analytics.
* charging sessions.
* charging efficiency.

---

## Trips

If reliable API support exists:

* trip history.
* trip distance.
* trip consumption.
* trip statistics.
* trip start/end information.

---

## Location

Potential:

* geofencing.
* home detection.
* work detection.
* arrival events.
* departure events.
* location-based automation.

---

## Automation

Potential:

* advanced charging automation.
* climate automation.
* vehicle arrival automation.
* vehicle departure automation.
* notification rules.
* maintenance reminders.

---

## Vehicle Compatibility

The plugin should gradually support additional Škoda vehicles as their MyŠkoda API representations become available.

The architecture should avoid model-specific assumptions wherever possible.

Potential future direction:

```text
MyŠkoda
│
├── Octavia
├── Superb
├── Kodiaq
├── Karoq
├── Enyaq
└── Future supported vehicles
```

Actual compatibility remains dependent on the API.

---

# What Will NOT Be Done Automatically

The plugin will not expose every field returned by the API simply because it exists.

A value should become a Domoticz device only when it is:

* useful;
* sufficiently stable;
* understandable;
* semantically meaningful;
* supported by a suitable Domoticz device type.

This prevents the integration from becoming an unmaintainable collection of raw API fields.

---

# Development Principles

These principles apply throughout the project.

## 1. Preserve existing devices

Existing Domoticz unit/IDX assignments are treated as compatibility contracts.

## 2. Provision idempotently

Running the plugin repeatedly must not create duplicate devices.

## 3. Preserve good data

Temporary API failures must not unnecessarily destroy valid last-known state.

## 4. Separate read and write operations

Telemetry and remote commands must remain clearly separated.

## 5. Verify commands

A successful HTTP request is not automatically a successful vehicle operation.

## 6. Prefer native Domoticz types

Use the correct Domoticz sensor/device representation whenever possible.

## 7. Normalize API data

Raw MyŠkoda responses should not leak directly into the Domoticz device layer.

## 8. Expect API evolution

Optional fields, partial responses and API changes must be handled gracefully.

## 9. Keep dependencies minimal

The standard Python library should remain the default unless an external dependency provides substantial value.

## 10. Stability before features

Especially from `0.8.x` onward, reliability and upgrade safety take priority over adding more telemetry.

## 11. Never make unsupported assumptions

If the MyŠkoda API does not reliably expose a capability, the plugin should not pretend that it does.

---

# Version Strategy

```text
0.4.x
 │
 ├── Stabilize the existing Beta
 │
 ▼
0.5.x
 │
 ├── Complete read-only integration
 │
 ▼
0.6.x
 │
 ├── Verified remote commands
 │
 ▼
0.7.x
 │
 ├── Automation and advanced vehicle features
 │
 ▼
0.8.x
 │
 ├── Multi-vehicle
 ├── Maintenance
 └── Historical/advanced data
 │
 ▼
0.9.x
 │
 ├── Feature freeze
 ├── Testing
 ├── Compatibility
 ├── Documentation
 └── Release Candidate
 │
 ▼
1.0.0
 │
 └── Production Stable
 │
 ▼
1.x
    └── New capabilities without breaking existing installations
```

---

# Release Philosophy

The project should evolve in three distinct phases.

## 0.4.x — Stabilize

Make the current architecture safe.

## 0.5–0.8 — Expand

Complete telemetry, introduce commands and then advanced functionality.

## 0.9–1.0 — Harden

Stop adding major features and prove that the plugin is reliable.

---

# Final Goal

The long-term goal of **Domoticz-MySkodaAPI** is not simply to expose the largest possible number of MyŠkoda API fields.

The goal is to provide:

> **A reliable, maintainable, upgrade-safe and Domoticz-native bridge between the MyŠkoda Public API and home automation.**

The desired evolution is:

```text
Experimental integration
        ↓
Structured API client
        ↓
Normalized vehicle model
        ↓
Reliable telemetry
        ↓
Stable Domoticz devices
        ↓
Complete read-only integration
        ↓
Verified vehicle commands
        ↓
Automation
        ↓
Advanced vehicle integration
        ↓
Release Candidate
        ↓
Production Stable 1.0
        ↓
Long-term 1.x development
```

---

# Status Legend

| Status              | Meaning                                    |
| ------------------- | ------------------------------------------ |
| **Released**        | Already implemented in a published release |
| **Planned**         | Intended development target                |
| **Potential**       | Possible future functionality              |
| **API-dependent**   | Depends on MyŠkoda API capabilities        |
| **Deferred**        | Deliberately postponed                     |
| **Not implemented** | Not currently available                    |

---

# Current Next Step

**Next milestone: `0.4.2`**

The immediate priority is **stability of the existing device/provisioning model**, especially safe device characteristic migration and upgrade handling.

Only after that foundation is reliable should development proceed toward the `0.5.x` complete read-only milestone.

