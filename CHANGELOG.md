# Changelog

All notable changes to **Domoticz-MySkodaAPI** are documented in this file.

The project follows [Semantic Versioning](https://semver.org/) where practical.

* **Alpha** releases are development releases and may contain architectural or device-model changes.
* **Beta** releases are intended for real-world use but may still introduce changes before `1.0.0`.
* **`1.0.0`** will mark the first production-stable release with a frozen device model and a strong commitment to upgrade compatibility.
* **Tag format, as of `0.4.3.2`:** release tags are plain numeric (`MAJOR.MINOR.PATCH` or `MAJOR.MINOR.PATCH.BUILD`, optionally `v`-prefixed) - no `-alpha`/`-beta`/build-number suffixes. This is required by PyPluginStore's release-channel tag matcher (`^v?[0-9]+(?:\.[0-9]+){1,3}$`); a suffixed tag is simply invisible to it, so the plugin would stay Git-only there forever. Pre-release iteration now happens as unreleased commits on `development`, not as tagged alpha builds.

---

# Release History

## [0.4.4.002] - 2026-10-04

Second remote-command release: two more writable commands, confirmed against the real OpenAPI spec and built on the same enabled/PIN/revert-on-failure pattern as Air Conditioning Control (0.4.4.0).

### Added

* **Unit 50 - Active Ventilation Control**: new writable Selector (On/Off). `POST {vehicle}/active-ventilation/start` and `.../stop` - confirmed against the spec that neither endpoint takes a request body or a security PIN.
* **Unit 51 - Auxiliary Heating Control**: new writable Selector (On/Off). `POST {vehicle}/auxiliary-heating/start` requires a Security PIN (`spin`, schema `StartAuxiliaryHeatingConfiguration`); `.../stop` does not.
* New hardware setting **Mode5 - "Auxiliary Heating PIN (S-PIN)"** (password-masked, optional, default empty). Read deliberately without `.strip()`, so a legitimately-entered PIN is never silently altered. Never written to any log line, even at Debug/Verbose level - covered by a dedicated regression test asserting a distinctive PIN value never appears in any debug call.
* `active_ventilation_active` and `auxiliary_heating_active` derived booleans in `vehicle.py`, mapping the richer read-side enums (`ActiveVentilation.state`, `AuxiliaryHeating.state`) onto the On/Off selector range, following the same pattern as `air_conditioning_active` from 0.4.4.0.
* Shared `_on_control_command()` / `_restore_control()` implementation in `plugin.py`, generalizing the command-dispatch flow (enabled check, API-ready check, an optional extra precondition, the actual call, rate-limit header bookkeeping, optimistic selector update or revert-on-failure) across all three `*_control` units. Per-feature specifics (log wording, the Auxiliary Heating PIN precondition) are supplied via small `start()`/`stop()` closures instead of duplicating the flow three times.
* 20 new regression tests: request-shape and PIN-masking tests for both new API methods, derived-boolean mapping tests for both new enums, and full command-dispatch tests (success, disabled, and the PIN-precondition path) for both new units.

### Fixed

* A direction-unaware precondition check: the generalized `extra_check` callback was being invoked without knowing whether the command was a start or a stop, so the Auxiliary Heating PIN requirement was blocking the *stop* command too whenever no PIN was configured - even though the spec only requires the PIN to *start* auxiliary heating. Caught by a new test (`test_auxiliary_heating_stop_command_does_not_require_a_pin`) before this was shipped; fixed by passing the start/stop direction into the check, so only the start path can be blocked on a missing PIN.

### Notes

* Exercised against a real vehicle end-to-end: the command pipeline, level-to-start/stop mapping, and PIN-masking in the log all behaved correctly. The vehicle itself returned `429 vehicle-not-accepting-requests` after exhausting all 3 retries - a vehicle-side throttle the API documents as caused by either the vehicle pacing its own request rate or a low 12V battery, not a plugin bug. As always, not every vehicle supports every operation - check **Unit 41 - Supported Operations** before assuming a failure is this plugin's fault.

## [0.4.4.001] - 2026-10-04

Logging/diagnostics release, prompted by a real report of "nothing happens" when clicking Air Conditioning Control in Domoticz - which turned out to be the **Debug** hardware setting (Mode6) never actually being wired to Domoticz's own debug flag, so no Debug-level log line could ever appear regardless of that dropdown.

### Fixed

* `Domoticz.Debugging()` is now actually called from the Mode6 setting on startup - previously set but never applied.

### Added

* Unconditional `onCommand` entry logging: every command Domoticz sends is now logged at Log level the moment it's received, regardless of the Debug setting, so a "nothing happens" report can always be diagnosed from the log alone.
* A top-level exception safety net in `onCommand`, so an unexpected error during command handling is logged instead of silently swallowed.
* Startup logging stating which Domoticz unit is Air Conditioning Control and whether remote commands are currently enabled.
* Error logging when a device update targets a missing/uncreated Domoticz device - previously a silent no-op.

## [0.4.4.0] - 2026-10-03

First remote-command release: the plugin can now optionally send a real vehicle command instead of only reading telemetry.

### Added

* **Unit 49 - Air Conditioning Control**: first writable Domoticz Selector (On/Off). `POST {vehicle}/air-conditioning/start` (body: `targetTemperature`, defaulting to 21°C) and `.../stop`.
* New hardware setting **Mode4 - "Enable Remote Commands"** (Off/On, default Off) - all `*_control` units stay inert, reverting any click back to the last known state, until this is explicitly turned on.
* `air_conditioning_active` derived boolean in `vehicle.py`, collapsing the 8-value `AirConditioning.state` enum (`OFF`, `COOLING`, `HEATING`, `HEATING_AUXILIARY`, `VENTILATION`, `COMPLETED`, `UNKNOWN`, `UNSUPPORTED`) onto the Selector's On/Off range.
* Rate-limit header bookkeeping (`RateLimit-*`/`X-API-Key-Expires-At`) extended to command responses, not just the main telemetry poll.

### Fixed

* Reconciled against the real MySkoda OpenAPI spec after initial development: `air-conditioning/start` requires a request body (initially sent without one); confirmed the Security PIN (`spin`) field belongs only to `auxiliary-heating/start`'s schema, not to air conditioning.

### Notes

* Exercised against a real vehicle: the command pipeline worked end-to-end, but the vehicle returned `422 operation-not-supported` for air conditioning - a vehicle-capability limit, not a plugin defect, separately confirmed by **Unit 40 - API Data Errors** flagging `AIR_CONDITIONING_UNSUPPORTED` for that same vehicle.

## [0.4.3.2] - 2026-09-30

First release published under a PyPluginStore-compatible tag - supersedes the three `0.4.3.1-00N-alpha` dated entries below (2026-09-19/22/25), none of which were ever visible to PyPluginStore's release channel because of their tag suffix. No functional changes beyond what those three entries already describe; this release exists to fix the tag format itself, not to ship new behavior.

### Changed

* Versioning scheme switched to plain numeric tags going forward (see the policy note above). `0.4.3.1-001/002/003-alpha` remain as historical tags/entries; nothing about their content changes.

### Verified (PyPluginStore readiness)

* `plugin.py` is at the repository root with a stable `key="MySkodaAPI"`, matching what a `registry.json` `domoticz_key` entry requires.
* Source scanned against PyPluginStore's AST security-scanner trigger list (`os.system`, `subprocess` with `shell=True`, `eval`, `exec`, `pickle`, `shutil.rmtree`, `os.remove`) - none present anywhere in the codebase.
* No third-party dependencies (`requirements.txt` is comment-only), so there's nothing for `uv`/`pip` dependency installation to fail on.

## [0.4.3.1-003-alpha] - 2026-09-25

MySkoda API v1.1.0 release: `charging.status` now optionally carries the plug state directly, rather than requiring it to be inferred from the derived charging state alone.

### Added

* New optional API fields handled: `status.plugConnectionState` (`CONNECTED`/`DISCONNECTED`) and `status.plugLockState` (`LOCKED`/`UNLOCKED`).
* **Unit 48 - Plug Lock State**: new read-only Selector device (`Unknown`/`Locked`/`Unlocked`), reusing the existing `selector_security_lock` mode already defined for `doors_locked`. Appended after unit 47, existing units 1-47 unchanged.
* 5 new regression tests covering both fields, including the case where `plugConnectionState` and the derived state would otherwise disagree.

### Changed

* **Unit 33 - Charging Connected**: `plugConnectionState` is now the preferred, authoritative source, used ahead of the existing heuristic that inferred connection state from the derived charging state (`CONNECT_CABLE`/`CHARGING`/`READY_FOR_CHARGING`). That heuristic is kept as a fallback for responses without this field, since it's documented as optional.
* `verify_charging_fields.py` now also checks for `plugConnectionState`/`plugLockState` in a captured dump, and `restore_selector()` in `devices.py` now handles unit 48 (so manually clicking the selector in the Domoticz UI reverts it to the real cached value, consistent with the other read-only selectors).

### Notes

* The v1.1.0 release notes also clarify that an *omitted* derived charging state must never be read as "disconnected", and that new derived-state values may be added over time. Both were already true of this plugin's existing fallback logic (it only acts on explicitly recognized states, and treats an absent state as unknown rather than disconnected) - no behavior change was needed there, only confirmation that it already matched the API's guarantees.
* `Charge Type` (unit 47) remains unconfirmed - unrelated to this release; still no real dump contains a `type`/`chargeType` key.

## [0.4.3.1-002-alpha] - 2026-09-22

Documentation-only build - no functional code changes since `0.4.3.1-001-alpha`. All 29 tests unchanged.

### Added

* `README.md`: split **Supported vehicles** into two tables. The existing tested table (Octavia 4 Facelift, Kodiaq II PHEV, Karoq Sportline) is unchanged. New **Known-compatible models** table lists vehicles Škoda's own MyŠkoda app description confirms have MyŠkoda/Connect support at all (Enyaq, Enyaq Coupé, Elroq, Scala, Kamiq, Fabia Mk4, Octavia iV, Superb/Superb iV, Karoq 2020+) - a prerequisite for reaching this plugin's API, independent of whether the JSON shape has been confirmed. Explicitly marked as untested with this plugin; model codes left blank (`—`) rather than guessed, since only Octavia (`NX`), Kodiaq II (`PS`) and Karoq (`NU`) have been properly sourced so far.

## [0.4.3.1-001-alpha] - 2026-09-19

Renamed from the plain `0.4.3.1` tag used earlier today, back to an alpha pre-release identifier - issue #9 (below) came in before that release had been confirmed by anyone, so it's being folded into this same version rather than shipped as a separate `0.4.3.2`. Supersedes the three `0.4.3-alpha` dated entries further below (2026-09-16/17/18). Consolidates: the PHEV nested `charging.status`/`charging.settings` parsing fix, the `remaining_charging_time` confirmation, the `CHARGING` -> connected inference, and the fixes below.

### Fixed

* **Issue #9**: `Remaining Charging Time` (unit 46) stayed stuck on its last real value long after a charge session had ended. Root cause: a third real dump from the same plug-in-hybrid Kodiaq, captured right after charging stopped (`state: "READY_FOR_CHARGING"`, `chargePowerInKw: 0.0`), showed that `remainingTimeToFullyChargedInMinutes` disappears from the API response entirely once a session ends - it isn't reported as `0`. Since the device-update code intentionally skips writes on missing/`None` values (to avoid clobbering good data with transient gaps), the device just never got updated again. Fixed by resetting `remaining_charging_time` to `0` whenever a known state other than `CHARGING` is seen and the key is absent; a genuinely unknown state (no `state` key found at all) is left untouched rather than guessed.
* `Charging Connected` now also infers `True` for `READY_FOR_CHARGING` (cable still connected right after a session ends), alongside the existing `CONNECT_CABLE` -> `False` and `CHARGING` -> `True` inferences.
* Added regression tests `test_phev_ready_for_charging_resets_remaining_time` and `test_remaining_charging_time_not_guessed_on_unknown_state`.

### Added

* `README.md`: new **Supported vehicles** section listing models/powertrains that have been exercised against a real captured API response ("Checked") versus ones still assumed to work ("In development").
* Ongoing test coverage now also includes a Karoq Sportline 2.0 TFSI 140kW (MY2020) - a non-PHEV vehicle, so it mainly exercises the base telemetry path rather than the charging-specific fixes above.

### Notes

* `Charge Type` (unit 47) remains unconfirmed - none of the three real dumps captured so far (`CONNECT_CABLE`, `CHARGING`, `READY_FOR_CHARGING`) contain a `type`/`chargeType` key anywhere under `charging`.

## [0.4.3-alpha] - 2026-09-18

### Fixed

* Confirmed `Remaining Charging Time` (`charging.status.remainingTimeToFullyChargedInMinutes`) against a second real dump from the same plug-in-hybrid Kodiaq, taken mid-charge - it was only a best guess as of 2026-09-17. No candidate-list change was needed; the nested path was already the first candidate and matched exactly.
* `Charging Connected` now also infers `True` when `charging.status.state` is `CHARGING` (a car can't be charging without being connected), alongside the existing `CONNECT_CABLE` -> `False` inference. Other states remain `Unknown`.
* Added a regression test (`test_phev_charging_active_confirms_remaining_time_and_connected`) covering the mid-charge payload.

### Notes

* `Charge Type` is still unconfirmed - neither the idle nor the mid-charge dump contains a `type`/`chargeType` key anywhere under `charging`. It's possible this endpoint doesn't expose AC/DC type at all; worth revisiting whether that device should stay in 0.4.3 if no key ever turns up.
* The mid-charge dump also revealed two fields not currently surfaced anywhere: `charging.status.chargingRateInKilometersPerHour` (62.0 in this case) and `charging.status.fullyChargedAt` (an ISO timestamp). Not wired up - flagging in case they're worth their own devices later.

## [0.4.3-alpha] - 2026-09-17

### Fixed

* Fixed all EV-related devices (units 30-35, 45-47) reading empty/zero on plug-in-hybrid vehicles. A real API dump from a plug-in-hybrid Kodiaq (reported via GitHub issue) showed the `charging` object nests data under `charging.status` (`battery`, `chargePowerInKw`, `state`) and `charging.settings` (`targetStateOfChargeInPercent`, `preferredChargeMode`), rather than as flat keys directly under `charging` as the parsing in `vehicle.py` assumed.
* `Electric Range` now correctly converts `status.battery.remainingCruisingRangeInMeters` from meters to km, and falls back to `fuelStatus.secondaryEngineRange.remainingRangeInKm` (already in km) when charging status isn't populated - both confirmed against the same dump.
* `Charging Connected` now infers `False` when `charging.status.state` is `CONNECT_CABLE`, the one state value whose meaning is unambiguous from the dump; other states are left `Unknown` rather than guessed.
* All existing flat-key candidates are kept alongside the new nested ones, so a response shape that has them flat still works.
* Added regression tests (`test_phev_nested_charging_status_settings`, `test_phev_electric_range_falls_back_to_fuel_status`) covering the real payload shape from the issue.

### Notes

* `Remaining Charging Time` and `Charge Type` were not visible in the captured dump (it was cut off before reaching them); their candidate lists were extended with the same `status.*` nesting pattern as a best guess only. `verify_charging_fields.py` was updated to check nested paths and print `fuelStatus.secondaryEngineRange` - re-run it against a hybrid vehicle to confirm these two before trusting them.

## [0.4.3-alpha] - 2026-09-16

### Changed

* Units 24 (Today Distance) and 25 (Yesterday Distance) are now Custom Sensors instead of RFXMeter counters.
* Unit 12 (Odometer / Mileage) remains the cumulative RFXMeter counter used for Domoticz distance statistics.
* This prevents negative counter peaks when the daily distance values reset at local midnight.

## [0.4.3] - 2026-09-13

### Added

* Three new read-only devices, using the `charging` data already fetched by `0.4.2` (no new `API_INCLUDE` entry, no extra API call, no rate-limit impact):
  * `Charging Power` (kW) - unit 45
  * `Remaining Charging Time` (min) - unit 46
  * `Charge Type` (AC/DC) - unit 47
* Existing units `1-44` are unchanged; new units are appended, matching the `0.4.2` upgrade-compatibility convention.

### Notes

* The field names used to parse power/remaining-time/charge-type from the API's `charging` object are best-guess candidates and have not yet been confirmed against a captured raw response. Verify before relying on these values in production.

## [0.4.2] - 2026-09-11

### Changed

* Production cleanup release based on `0.4.1`.
* The 44 devices are no longer dropped/recreated on launch. 
* Redesign of the device.py 
* Documentation was aligned with the actual `0.4.2` plugin configuration and device model.
* Domoticz units `1–44` remain unchanged.
* The read-only telemetry model remains unchanged.

## [0.4.1] - 2026-09-08

### First Stable Beta

The first release considered suitable for longer-running real-world use.

### Changed

* Production cleanup release based on `0.4.0-alpha.3`.
* API Status now includes the HTTP return code.
* API Status also reports the RFC problem type when supplied by the MyŠkoda API, including:

  * `rate-limit-exceeded`
  * `vehicle-not-accepting-requests`
* Documentation was aligned with the actual `0.4.1` plugin configuration and device model.
* Domoticz units `1–44` remain unchanged.
* The read-only telemetry model remains unchanged.

### Repository

* Added repository hygiene rules for:

  * runtime state
  * generated archives
  * Python cache files
  * local editor files

### Compatibility

* Existing Domoticz unit numbers are preserved.
* No vehicle commands are sent to MyŠkoda.
* Existing installations can continue using the established telemetry model.

### Known Issues

* Changing Domoticz device characteristics during an upgrade can still cause the plugin to crash in some circumstances.
* Device migration and device-type changes therefore require additional hardening before the project can be considered production-stable.

See GitHub issue #6 for the current device-type migration problem.

---

## [0.4.0-alpha.3] - 2026-09-05

### Added

* Added unit `44` — **API Key Status**.

* Implemented the sensor as a native Domoticz General/Alert sensor.

* Added API-key status levels:

  * `OK`
  * `WARNING`
  * `EXPIRED`
  * `UNKNOWN`

* Added configurable warning threshold through:

  `API_KEY_EXPIRY_WARNING_DAYS`

* Default warning threshold is **30 days**.

### Compatibility

* Unit `21` — **API Key Expiry** remains available as a numeric days-remaining Custom Sensor.
* Existing device units remain unchanged.

---

## [0.4.0-alpha.2] - 2026-09-05

### Changed

* Vehicle Captured is now represented as elapsed seconds since the vehicle capture timestamp supplied by the API.
* API Key Expiry is now represented as numeric days remaining.
* Added configurable API-key expiry warning threshold.
* Default warning threshold is 30 days.
* API Status now includes the HTTP return code and its meaning.

### Added

* Unit `42` — **API Rate Remaining**.
* Unit `43` — **API Rate Reset In**.

---

## [0.4.0-alpha.1]

### Changed

* Replaced semantic Text state devices with native Domoticz Selector Switch devices for vehicle-state telemetry.
* Preserved existing Domoticz unit numbers `1–41`.
* Added automatic migration for affected existing devices.
* Selector Switch controls remain telemetry-only.
* Selector controls do **not** send commands to the vehicle.

### Added

* Target Temperature is represented as a read-only Domoticz Custom Sensor.
* Target Temperature uses degrees Celsius (`°C`).

### Design Principle

The Selector Switch implementation provides a native Domoticz representation of vehicle states while deliberately keeping the integration read-only.

---

## [0.3.0-alpha4] - 2026-09-05

### Release

* Released the `0.3.0-alpha4` development milestone.
* Continued the transition toward a more complete and structured vehicle telemetry model.

### Note

This release formed part of the rapid architecture and telemetry development leading to the `0.4.x` beta series.

---

## [0.0.4-alpha]

### Added

Expanded the normalized vehicle telemetry model with:

* charging state
* battery state of charge
* electric range
* charging connection
* target state of charge
* charge mode where supported
* engine/fuel type
* telemetry capture timestamps
* API partial-data error reporting
* API capability summary
* supported-operation reporting

### Design

* Integration remains read-only.
* No vehicle commands are issued.

---

## [0.0.3.5-alpha.4]

### Changed

* Changed **Fuel Range** to a Domoticz Custom Sensor.
* Changed **Total Range** to a Domoticz Custom Sensor.
* Explicitly use `km` as the unit.
* Preserved existing Domoticz unit numbers.

---

## [0.0.3.5-alpha.3]

### Added

* Added Custom Sensor handling for range values.
* Added migration support for affected Domoticz devices.

---

## [0.0.3.5-alpha.2]

### Added

* Added semantic smart-state handling for vehicle telemetry.
* Improved the interpretation of vehicle state values before publishing them to Domoticz.

---

## [0.0.3.5-alpha.1]

### Added

* Added persistent odometer state.
* Added daily distance delta calculation.
* Added **Today's Distance**.
* Added **Yesterday's Distance**.

### Changed

* Completed daily distance is rolled into Yesterday Distance at local midnight.
* Negative odometer changes are ignored.
* Implausibly large odometer jumps are ignored.

### Design

The plugin now maintains a small amount of local state in order to provide useful derived vehicle information rather than simply exposing raw API values.

---

## [0.0.3.5-alpha]

### Changed

* Improved Domoticz device types.
* Improved telemetry presentation.
* Continued migration toward semantically correct Domoticz devices.

---

## [0.0.3-alpha.1]

### Fixed

* Corrected MyŠkoda Public API authentication to use:

  `X-API-Key`

* Corrected parsing of the current MyŠkoda API response under the `vehicle` object.

### Added

* API-key expiry header parsing.
* API rate-limit response header parsing.

---

## [0.0.3-alpha]

### Added

* HTTP `429` retry handling.
* Transient HTTP `5xx` retry handling.
* `Retry-After` support.
* Exponential backoff.
* API error classification.
* API rate-limit metadata.
* Last-known-good vehicle-state caching.

### Compatibility

* Existing Domoticz unit IDs remain unchanged.

### Reliability

Temporary MyŠkoda API failures no longer have to result in immediate loss of the previously known vehicle state.

---

## [0.0.2-alpha]

### Architecture

Introduced the refactored plugin architecture with separate responsibilities for:

* API communication
* vehicle-state processing
* Domoticz device management
* utilities
* constants

### Compatibility

* Preserved the original Domoticz units `1–23`.

### Design

* Integration remains read-only.
* Project remains standard-library based.
* API and Domoticz responsibilities are separated to allow future expansion.

---

## [0.0.1.1-alpha] - 2026-09-04

### Development Release

* First intermediate development release following the initial beta.
* Established the foundation for the subsequent API, telemetry and architecture refactoring.

---

## [0.0.1-beta] - 2026-09-02

### First Long-Running Beta

* Adjusted Domoticz device definitions.
* Established the first long-running beta implementation.
* Began the transition from an experimental integration toward a continuously running Domoticz plugin.

---

# Current Status

## 0.4.1 — First Stable Beta

The project currently provides a **read-only MyŠkoda telemetry integration for Domoticz**.

The current architecture includes:

* MyŠkoda API communication
* API-key authentication
* retry and backoff handling
* rate-limit handling
* last-known-good state handling
* normalized vehicle telemetry
* battery information
* charging information
* fuel and range information
* odometer tracking
* daily distance calculation
* vehicle-state telemetry
* climate-related telemetry
* API diagnostics
* API-key expiry monitoring
* API rate-limit monitoring
* native Domoticz device types
* device migration support
* stable Domoticz unit numbering

The project currently remains **read-only** with respect to the vehicle.

---

# Versioning Policy

The project uses Semantic Versioning where practical.

* Patch releases (`x.y.Z`) are intended for fixes, documentation corrections and maintenance.
* Minor releases (`x.Y.0`) may introduce new functionality while maintaining the established architecture and compatibility expectations.
* Alpha releases may introduce device-model or architectural changes.
* Beta releases should be suitable for real-world use but may still introduce changes before `1.0.0`.
* `1.0.0` will represent the first production-stable release with a frozen device model and a strong commitment to upgrade compatibility.

---

