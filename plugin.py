#!/usr/bin/env python3

"""
<plugin key="MySkodaAPI" name="MySkoda API Integration" author="Jan Reimen" version="0.4.4.1" externallink="https://github.com/janreimen/Domoticz-MySkodaAPI">
  <description>
    <h2>MySkoda API Integration</h2><br/>
    Integration with the official Škoda MySkoda Public API: telemetry is always read-only; remote vehicle commands (Air Conditioning, Active Ventilation and Auxiliary Heating Control) are opt-in and off by default. Not every vehicle supports every command - check the "Supported Operations" device for this vehicle before relying on one.<br/>
    API key and VIN are stored in the Domoticz hardware configuration. Auxiliary Heating additionally requires the vehicle's own Security PIN (S-PIN), entered below - it is never needed for Air Conditioning or Active Ventilation.<br/>
  </description>
  <params>
    <param field="Mode1" label="API Key" width="500px" required="true" password="true" default="" />
    <param field="Mode2" label="VIN" width="300px" required="true" default="" />
    <param field="Mode3" label="Poll Interval (minutes)" width="80px" required="true" default="30" />
    <param field="Mode4" label="Enable Remote Commands" width="120px">
      <options>
        <option label="Off" value="0" default="true" />
        <option label="On" value="1" />
      </options>
    </param>
    <param field="Mode5" label="Auxiliary Heating PIN (S-PIN)" width="150px" password="true" default="" />
    <param field="Mode6" label="Debug" width="120px">
      <options>
        <option label="Off" value="0" default="true" />
        <option label="Basic" value="1" />
        <option label="Verbose" value="2" />
      </options>
    </param>
  </params>
</plugin>
"""

import os
import time
import Domoticz

from datetime import datetime, timezone

from constants import (
    DEFAULT_AC_TARGET_TEMPERATURE_CELSIUS, DEFAULT_POLL_MINUTES, MAX_POLL_MINUTES, MIN_POLL_MINUTES,
    PLUGIN_VERSION, STATE_CACHE_FILENAME, DISTANCE_STATE_FILENAME, API_KEY_EXPIRY_WARNING_DAYS,
    UNITS, WRITABLE_UNITS,
)
from devices import DeviceManager
from myskoda_api import MySkodaAPI
from utils import clamp, load_json, safe_int, save_json_atomic, safe_str
from vehicle import VehicleState


class Logger:
    def Debug(self, message):
        Domoticz.Debug(str(message))

    def Log(self, message):
        Domoticz.Log(str(message))

    def Error(self, message):
        Domoticz.Error(str(message))


class BasePlugin:
    def __init__(self):
        self.logger = Logger()
        self.api = None
        self.devices = None
        self.poll_minutes = DEFAULT_POLL_MINUTES
        self.commands_enabled = False
        self.last_poll = 0.0
        self.last_success = 0.0
        self.failure_count = 0
        self.next_retry_at = 0.0
        self.cache_path = None
        self.cached_state = None
        self.distance_state = {
            "date": None,
            "last_odometer": None,
            "today_distance": 0.0,
            "yesterday_distance": 0.0,
        }
        self.distance_path = None
        self.api_status = "STARTING"
        self.data_quality = "UNKNOWN"
        self.api_rate = "Unavailable"
        self.api_key_expiry = "Unknown"
        self.api_key_expiry_days = None
        self.vehicle_captured_at = None
        self.rate_remaining = None
        self.rate_reset_at = None
        self.debug_level = 0
        self.auxiliary_heating_pin = ""

    def _parse_config(self):
        api_key = safe_str(Parameters.get("Mode1", "")).strip()
        vin = safe_str(Parameters.get("Mode2", "")).strip()
        poll = safe_int(Parameters.get("Mode3", DEFAULT_POLL_MINUTES), DEFAULT_POLL_MINUTES)
        poll = clamp(poll or DEFAULT_POLL_MINUTES, MIN_POLL_MINUTES, MAX_POLL_MINUTES)
        commands_enabled = safe_str(Parameters.get("Mode4", "0")).strip() == "1"
        # Not stripped: a PIN is an opaque credential, not text - trimming
        # whitespace a user may have genuinely typed would silently send a
        # different PIN than the one configured.
        auxiliary_heating_pin = safe_str(Parameters.get("Mode5", ""))
        debug_level = safe_int(Parameters.get("Mode6", "0"), 0)
        if not api_key:
            raise ValueError("API Key is not configured")
        if not vin:
            raise ValueError("VIN is not configured")
        self.poll_minutes = poll
        self.commands_enabled = commands_enabled
        self.auxiliary_heating_pin = auxiliary_heating_pin
        self.debug_level = debug_level
        return api_key, vin

    def _cache_load(self):
        if not self.cache_path:
            return
        data = load_json(self.cache_path, {})
        state_data = data.get("state") if isinstance(data, dict) else None
        if isinstance(state_data, dict):
            self.cached_state = VehicleState.from_dict(state_data)
            self.logger.Debug("Loaded last-known-good vehicle state from cache")

    def _distance_load(self):
        if not self.distance_path:
            return
        data = load_json(self.distance_path, {})
        if not isinstance(data, dict):
            return
        self.distance_state["date"] = safe_str(data.get("date"), None)
        self.distance_state["last_odometer"] = data.get("last_odometer")
        self.distance_state["today_distance"] = float(data.get("today_distance", 0.0) or 0.0)
        self.distance_state["yesterday_distance"] = float(data.get("yesterday_distance", 0.0) or 0.0)

    def _distance_save(self):
        if not self.distance_path:
            return
        save_json_atomic(self.distance_path, self.distance_state)

    def _update_distance_delta(self, odometer):
        """Accumulate positive odometer deltas by local calendar day.

        A restart does not create a delta because last_odometer is persisted.
        Negative jumps are ignored as invalid/reset readings.
        """
        if odometer is None:
            return self.distance_state["today_distance"], self.distance_state["yesterday_distance"]

        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            odo = float(odometer)
        except (TypeError, ValueError):
            return self.distance_state["today_distance"], self.distance_state["yesterday_distance"]

        stored_date = self.distance_state.get("date")
        last = self.distance_state.get("last_odometer")

        if stored_date != today:
            if stored_date is not None:
                self.distance_state["yesterday_distance"] = max(0.0, float(self.distance_state.get("today_distance", 0.0)))
            self.distance_state["date"] = today
            self.distance_state["today_distance"] = 0.0
            last = None

        if last is not None:
            try:
                delta = odo - float(last)
                if 0.0 <= delta <= 1000.0:
                    self.distance_state["today_distance"] += delta
                elif delta < 0:
                    self.logger.Debug("Ignoring negative odometer delta: {:.3f} km".format(delta))
                else:
                    self.logger.Debug("Ignoring implausibly large odometer delta: {:.3f} km".format(delta))
            except (TypeError, ValueError):
                pass

        self.distance_state["last_odometer"] = odo
        self._distance_save()
        return self.distance_state["today_distance"], self.distance_state["yesterday_distance"]

    def _cache_save(self, state):
        if not self.cache_path:
            return
        payload = {
            "version": PLUGIN_VERSION,
            "saved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "state": state.to_dict(),
        }
        try:
            save_json_atomic(self.cache_path, payload)
        except Exception as exc:
            self.logger.Error("Could not save state cache: {}".format(exc))

    @staticmethod
    def _parse_iso_timestamp(value):
        if not value:
            return None
        try:
            text = str(value).strip()
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            dt = datetime.fromisoformat(text)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except (TypeError, ValueError):
            return None

    def _api_key_status(self, expiry_dt, now=None):
        now = time.time() if now is None else now
        if expiry_dt is None:
            return {"level": 0, "state": "UNKNOWN", "text": "UNKNOWN — API key expiry is not available"}
        remaining_days = (expiry_dt.timestamp() - now) / 86400.0
        if remaining_days <= 0:
            return {"level": 4, "state": "EXPIRED", "text": "EXPIRED — API key has expired"}
        if remaining_days <= API_KEY_EXPIRY_WARNING_DAYS:
            return {"level": 2, "state": "WARNING", "text": "WARNING — API key expires in {:.1f} days (threshold: {} days)".format(remaining_days, API_KEY_EXPIRY_WARNING_DAYS)}
        return {"level": 1, "state": "OK", "text": "OK — API key expires in {:.1f} days".format(remaining_days)}

    def _derived_telemetry(self, now=None):
        now = time.time() if now is None else now
        captured_elapsed = None
        if self.vehicle_captured_at:
            captured_elapsed = max(0.0, now - self.vehicle_captured_at.timestamp())

        expiry_days = None
        expiry_dt = self._parse_iso_timestamp(self.api_key_expiry)
        api_key_status = self._api_key_status(expiry_dt, now)
        if expiry_dt:
            expiry_days = max(0.0, (expiry_dt.timestamp() - now) / 86400.0)

        rate_reset = None
        if self.rate_reset_at is not None:
            rate_reset = max(0.0, self.rate_reset_at - now)

        return captured_elapsed, expiry_days, rate_reset, api_key_status

    @staticmethod
    def _api_status_text(result):
        code = result.status
        if code is None:
            return "- Connection error"
        meanings = {
            200: "OK", 400: "Bad Request", 401: "Unauthorized / API key expired",
            403: "Forbidden / not authorized", 404: "Not Found", 409: "Conflict",
            422: "Unprocessable / unsupported or disabled", 429: "Too Many Requests",
            500: "Internal Server Error", 502: "Bad Gateway", 503: "Service Unavailable",
            504: "Gateway Timeout",
        }
        meaning = meanings.get(code, "HTTP error")
        text = "{} {}".format(code, meaning)
        problem_type = getattr(result, "problem_type", "")
        if problem_type:
            short_type = problem_type.rstrip("/").rsplit("/", 1)[-1]
            if short_type:
                text += " / " + short_type
        elif code == 429:
            text += " / rate limited"
        return text

    def _set_failure(self, result):
        self.failure_count += 1
        self.api_status = self._classify_error(result)
        delay = min(max(30.0, self.poll_minutes * 60.0), 3600.0)
        delay *= min(2 ** max(0, self.failure_count - 1), 4)
        if result.retry_after is not None:
            delay = max(delay, result.retry_after)
        self.next_retry_at = time.time() + min(delay, 3600.0)

    @staticmethod
    def _classify_error(result):
        if result.status in (401, 403):
            return "AUTH_ERROR"
        if result.status == 429:
            return "RATE_LIMITED"
        if result.status in (500, 502, 503, 504):
            return "API_ERROR"
        if result.status is None:
            return "CONNECTION_ERROR"
        if result.status == 200 and result.data is None:
            return "INVALID_DATA"
        return "API_ERROR"

    def _record_api_headers(self, result, now=None):
        """Update the plugin's rate-limit/API-key-expiry bookkeeping from an
        APIResult's headers. The real OpenAPI spec confirms the command
        endpoints (air-conditioning/start, /stop, ...) return the same
        RateLimit-*/X-API-Key-Expires-At headers as the main vehicle GET, so
        this is shared between _poll() and any command call rather than
        being specific to the polling path. onHeartbeat() already pushes
        these in-memory fields to the relevant devices periodically, so no
        direct device update is needed here.
        """
        if now is None:
            now = time.time()
        self.api_rate = result.rate_text
        self.rate_remaining = result.rate_remaining_value
        if result.rate_reset_value is not None:
            self.rate_reset_at = now + result.rate_reset_value
        if result.api_key_expires_at:
            self.api_key_expiry = result.api_key_expires_at

    def _poll(self):
        now = time.time()
        if now < self.next_retry_at:
            return
        self.last_poll = now
        self.logger.Debug("Polling MySkoda API")
        result = self.api.fetch_vehicle()
        self._record_api_headers(result, now)

        if not result.ok:
            self._set_failure(result)
            self.logger.Error("MySkoda API: {}".format(result.error))
            self.data_quality = "STALE" if self.cached_state is not None else "ERROR"
            if self.devices:
                self.devices.update_api_only(
                self._api_status_text(result), self.api_rate, self.data_quality, self.cached_state,
                api_rate_remaining=self.rate_remaining,
                api_rate_reset=max(0.0, self.rate_reset_at - time.time()) if self.rate_reset_at else None,
                api_key_status=self._api_key_status(self._parse_iso_timestamp(self.api_key_expiry), time.time()),
            )
            return

        try:
            state = VehicleState.from_api(result.data)
            if not state.vin:
                state.vin = self.api.vin
            self.cached_state = state
            self._cache_save(state)
            today_distance, yesterday_distance = self._update_distance_delta(state.odometer)
            self.last_success = now
            self.vehicle_captured_at = self._parse_iso_timestamp(state.captured_at)
            self.failure_count = 0
            self.next_retry_at = 0.0
            self.api_status = "OK"
            self.data_quality = "GOOD"
            captured_elapsed, expiry_days, rate_reset, api_key_status = self._derived_telemetry(now)
            self.api_key_expiry_days = expiry_days
            self.devices.update(
                state, self._api_status_text(result), self.api_rate, expiry_days,
                vehicle_captured_elapsed=captured_elapsed,
                api_rate_remaining=self.rate_remaining, api_rate_reset=rate_reset,
                api_key_status=api_key_status,
                today_distance=today_distance,
                yesterday_distance=yesterday_distance,
                data_quality=self.data_quality,
            )
            self.logger.Log("MySkoda API update successful")
        except Exception as exc:
            self.failure_count += 1
            self.api_status = "INVALID_DATA"
            self.next_retry_at = time.time() + min(self.poll_minutes * 60.0, 3600.0)
            self.logger.Error("Could not parse MySkoda API response: {}".format(exc))
            self.data_quality = "STALE" if self.cached_state is not None else "ERROR"
            self.devices.update_api_only(
                self._api_status_text(result), self.api_rate, self.data_quality, self.cached_state,
                api_rate_remaining=self.rate_remaining,
                api_rate_reset=max(0.0, self.rate_reset_at - time.time()) if self.rate_reset_at else None,
                api_key_status=self._api_key_status(self._parse_iso_timestamp(self.api_key_expiry), time.time()),
            )

    def _announce_command_unit(self, key, display_name, extra_note=""):
        """Log, on every startup, which Domoticz unit a writable command
        selector is and whether it will currently do anything - this is
        what caught the "wrong device clicked" and "commands disabled"
        confusions during testing, so every *_control unit gets one.
        """
        unit = UNITS[key]
        if not self.commands_enabled:
            self.logger.Log(
                "{} is Domoticz Unit {}, but remote commands are OFF - clicking it will "
                "be ignored and the selector reverted. Set 'Enable Remote Commands' to On "
                "in this hardware's settings to make it do anything.".format(display_name, unit)
            )
            return
        note = " " + extra_note if extra_note else ""
        self.logger.Log(
            "{} is Domoticz Unit {} (a Selector: Unknown/Off/On) - click it to send a real "
            "start/stop command to the vehicle.{}".format(display_name, unit, note)
        )

    def onStart(self):
        try:
            api_key, vin = self._parse_config()
        except ValueError as exc:
            self.logger.Error(str(exc))
            return

        # Wire the "Debug" hardware setting (Mode6) to Domoticz's own debug
        # flag - without this, Domoticz.Debug()/self.logger.Debug() calls
        # are suppressed no matter what the dropdown says, because nothing
        # ever told the Domoticz framework debug logging was wanted (this
        # was true of every released version up to and including 0.4.4.0).
        # Domoticz.Debugging() actually takes a bitmask of several internal
        # categories, not a simple on/off, and we don't rely on the exact
        # bit layout here - any non-zero Mode6 setting just asks for bit 1
        # (enables the plugin's own Debug() calls), which is the one thing
        # this plugin's "Basic"/"Verbose" choice needs to control for now.
        try:
            Domoticz.Debugging(1 if self.debug_level > 0 else 0)
        except Exception as exc:
            self.logger.Error("Could not set debug level: {}".format(exc))

        self.logger.Log("Starting MySkoda API Integration {}".format(PLUGIN_VERSION))
        self.logger.Log("Remote commands: {}".format("ENABLED" if self.commands_enabled else "disabled"))
        self.devices = DeviceManager(self.logger, Devices)
        self.devices.ensure_devices()
        self._announce_command_unit(
            "air_conditioning_control", "Air Conditioning Control",
            "Not every vehicle supports this - check the 'Supported Operations' device.",
        )
        self._announce_command_unit(
            "active_ventilation_control", "Active Ventilation Control",
            "Not every vehicle supports this - check the 'Supported Operations' device.",
        )
        if self.auxiliary_heating_pin:
            self._announce_command_unit(
                "auxiliary_heating_control", "Auxiliary Heating Control",
                "Not every vehicle supports this - check the 'Supported Operations' device.",
            )
        else:
            self.logger.Log(
                "Auxiliary Heating Control is Domoticz Unit {}, but no Security PIN (S-PIN) "
                "is configured - clicking it will be ignored. Set 'Auxiliary Heating PIN "
                "(S-PIN)' in this hardware's settings to use it.".format(
                    UNITS["auxiliary_heating_control"]
                )
            )
        home = Parameters.get("HomeFolder", ".")
        self.cache_path = os.path.join(home, STATE_CACHE_FILENAME)
        self.distance_path = os.path.join(home, DISTANCE_STATE_FILENAME)
        self._cache_load()
        self._distance_load()
        self.api = MySkodaAPI(api_key, vin, self.logger)
        self._poll()

    def onCommand(self, unit, command, level, hue):
        """Dispatch writable units (see WRITABLE_UNITS) to real vehicle
        commands; reject local changes on every other unit, since those
        devices remain telemetry-only.

        Domoticz selector widgets are inherently interactive, so a dashboard
        click always arrives here first regardless of whether the unit is
        meant to be actionable. For anything not in WRITABLE_UNITS, we
        deliberately do not translate the click into a vehicle/API command -
        we just restore the last API-derived state immediately when
        possible, same as always.
        """
        # Unconditional (not Debug) on purpose: this is the single most
        # useful line for diagnosing "I click the button and nothing
        # happens" - it proves whether Domoticz even called the plugin at
        # all, before anything else can go wrong. If a click never produces
        # this line in the Domoticz Log, the problem is on the Domoticz/
        # device side (wrong unit, device not writable, ...), not here.
        self.logger.Log("onCommand received: unit={} command={} level={} hue={}".format(unit, command, level, hue))

        try:
            if unit in WRITABLE_UNITS:
                self._on_writable_command(unit, command, level)
                return

            self.logger.Debug(
                "Ignoring read-only selector command unit={} command={} level={}".format(
                    unit, command, level
                )
            )
            if self.devices and self.cached_state is not None:
                self.devices.restore_selector(unit, self.cached_state)
            elif self.devices and self.cached_state is None:
                self.logger.Debug("Not restoring unit {}: no cached vehicle state yet".format(unit))
        except Exception as exc:
            # Last-resort safety net - an unexpected exception anywhere in
            # the dispatch chain must never disappear silently.
            self.logger.Error("onCommand failed for unit={} command={} level={}: {}".format(unit, command, level, exc))

    def _on_writable_command(self, unit, command, level):
        if unit == UNITS["air_conditioning_control"]:
            self._on_air_conditioning_command(level)
            return
        if unit == UNITS["active_ventilation_control"]:
            self._on_active_ventilation_command(level)
            return
        if unit == UNITS["auxiliary_heating_control"]:
            self._on_auxiliary_heating_command(level)
            return
        self.logger.Error("Unhandled writable unit {} (command={}, level={}) - ignoring".format(unit, command, level))

    def _on_control_command(self, key, display_name, level, start_fn, stop_fn, extra_check=None):
        """Shared flow behind every *_control selector (Air Conditioning,
        Active Ventilation, Auxiliary Heating): level follows
        SELECTOR_LEVELS (0=Unknown, 10=Off, 20=On - anything at or above ON
        is a start request, everything else a stop request), then the
        standard enabled/API-ready checks, an optional extra precondition
        (used by Auxiliary Heating's S-PIN requirement; called as
        extra_check(turning_on) so a direction-specific check - e.g. "only
        require the PIN when starting" - can see which way the command
        goes), the actual call via
        start_fn/stop_fn (each logs its own "Sending ..." line and returns
        an APIResult), shared rate-limit bookkeeping, and either an
        optimistic selector update or a revert on failure.
        """
        turning_on = level >= 20
        self.logger.Log("{} command: level={} -> {}".format(display_name, level, "START" if turning_on else "STOP"))

        if not self.commands_enabled:
            self.logger.Error(
                "{} command ignored: remote commands are disabled - set 'Enable Remote "
                "Commands' to On in the hardware settings to use this.".format(display_name)
            )
            self._restore_control(key)
            return
        if self.api is None:
            self.logger.Error("{} command ignored: API client is not ready yet".format(display_name))
            self._restore_control(key)
            return
        if extra_check is not None:
            block_reason = extra_check(turning_on)
            if block_reason:
                self.logger.Error("{} command ignored: {}".format(display_name, block_reason))
                self._restore_control(key)
                return

        result = start_fn() if turning_on else stop_fn()

        # Command responses carry the same RateLimit-*/X-API-Key-Expires-At
        # headers as the main poll (confirmed in the real spec), on both
        # success and failure - keep the bookkeeping current either way.
        self._record_api_headers(result)

        if result.ok:
            self.logger.Log("{} command accepted (HTTP {})".format(display_name, result.status))
            # Optimistic UI update - the next poll corrects this if the
            # vehicle doesn't actually end up where we expect.
            if self.devices:
                self.devices._update_selector(key, "ON" if turning_on else "OFF")
        else:
            # _api_status_text already turns a problem+json "type" URL (the
            # spec confirms operation-not-authorized for 403 and
            # operation-not-supported for 422 here) into a short slug, so
            # reuse it for a message consistent with the main poll path.
            # This is also the exact path that reported "Vehicle ... does
            # not support air conditioning" (operation-not-supported) when
            # tested against a real vehicle - a vehicle-capability limit,
            # not a plugin bug.
            message = "{} command failed: {}".format(display_name, self._api_status_text(result))
            if result.problem_detail:
                message += " - " + result.problem_detail
            elif result.error:
                message += " - " + result.error
            self.logger.Error(message)
            self._restore_control(key)

    def _on_air_conditioning_command(self, level):
        def start():
            self.logger.Log("Sending start-air-conditioning command (target {}\u00b0C)".format(DEFAULT_AC_TARGET_TEMPERATURE_CELSIUS))
            return self.api.start_air_conditioning(DEFAULT_AC_TARGET_TEMPERATURE_CELSIUS)

        def stop():
            self.logger.Log("Sending stop-air-conditioning command")
            return self.api.stop_air_conditioning()

        self._on_control_command("air_conditioning_control", "Air Conditioning Control", level, start, stop)

    def _on_active_ventilation_command(self, level):
        def start():
            self.logger.Log("Sending start-active-ventilation command")
            return self.api.start_active_ventilation()

        def stop():
            self.logger.Log("Sending stop-active-ventilation command")
            return self.api.stop_active_ventilation()

        self._on_control_command("active_ventilation_control", "Active Ventilation Control", level, start, stop)

    def _on_auxiliary_heating_command(self, level):
        def start():
            self.logger.Log("Sending start-auxiliary-heating command")
            return self.api.start_auxiliary_heating(self.auxiliary_heating_pin)

        def stop():
            self.logger.Log("Sending stop-auxiliary-heating command")
            return self.api.stop_auxiliary_heating()

        def check_pin(turning_on):
            # The spec only requires "spin" to START auxiliary heating -
            # stopping it takes no PIN at all, so don't block STOP here.
            if turning_on and not self.auxiliary_heating_pin:
                return (
                    "no Security PIN (S-PIN) is configured - set 'Auxiliary Heating PIN "
                    "(S-PIN)' in the hardware settings to use this"
                )
            return None

        self._on_control_command(
            "auxiliary_heating_control", "Auxiliary Heating Control", level, start, stop, extra_check=check_pin
        )

    def _restore_control(self, key):
        if self.devices is None:
            self.logger.Debug("Not restoring {}: devices not ready yet".format(key))
            return
        if self.cached_state is None:
            # No successful poll yet - there is nothing to revert to, so the
            # selector is left exactly where the user clicked it. From the
            # Domoticz UI this looks identical to "nothing happens"; this
            # line is what distinguishes that case from an actual bug.
            self.logger.Log(
                "Not restoring {}: no cached vehicle state yet "
                "(the selector will stay where you clicked it until the next successful poll)".format(key)
            )
            return
        try:
            self.devices.restore_selector(UNITS[key], self.cached_state)
        except Exception as exc:
            self.logger.Error("Could not restore {}: {}".format(key, exc))

    def onStop(self):
        self.logger.Log("Stopping MySkoda API Integration")

    def onHeartbeat(self):
        if self.api is None:
            return
        now = time.time()
        if self.devices and (self.cached_state is not None or self.vehicle_captured_at or self.api_key_expiry or self.rate_reset_at):
            captured_elapsed, expiry_days, rate_reset, api_key_status = self._derived_telemetry(now)
            if captured_elapsed is not None:
                self.devices._update_custom_numeric("vehicle_captured", captured_elapsed, self.devices.CUSTOM_SECONDS_OPTIONS)
            if expiry_days is not None:
                self.devices._update_custom_numeric("api_key_expiry", expiry_days, self.devices.CUSTOM_DAYS_OPTIONS, decimals=2)
            if self.rate_remaining is not None:
                self.devices._update_custom_numeric("api_rate_remaining", self.rate_remaining, self.devices.CUSTOM_REQUESTS_OPTIONS)
            if rate_reset is not None:
                self.devices._update_custom_numeric("api_rate_reset", rate_reset, self.devices.CUSTOM_SECONDS_OPTIONS)
            expiry_dt = self._parse_iso_timestamp(self.api_key_expiry)
            self.devices._update_alert("api_key_status", self._api_key_status(expiry_dt, now)["level"], self._api_key_status(expiry_dt, now)["text"])
        if now - self.last_poll >= self.poll_minutes * 60.0:
            self._poll()


_plugin = BasePlugin()


def onStart():
    _plugin.onStart()


def onStop():
    _plugin.onStop()


def onHeartbeat():
    _plugin.onHeartbeat()


def onCommand(unit, command, level, hue):
    _plugin.onCommand(unit, command, level, hue)
