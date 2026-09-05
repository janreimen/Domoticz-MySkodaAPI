#!/usr/bin/env python3

"""
<plugin key="MySkodaAPI" name="MySkoda API Integration" author="Jan Reimen" version="0.4.0-alpha.2"
    externallink="https://github.com/janreimen/Domoticz-MySkodaAPI">
<description>
<h2>MySkoda API Integration</h2><br/>
Read-only integration with the official Škoda MySkoda Public API.<br/>
API key and VIN are stored in the Domoticz hardware configuration.<br/>
</description>
<params>
<param field="Mode1" label="API Key" width="500px" required="true" password="true" default="" />
<param field="Mode2" label="VIN" width="300px" required="true" default="" />
<param field="Mode3" label="Poll Interval (minutes)" width="80px" required="true" default="30" />
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
    DEFAULT_POLL_MINUTES, MAX_POLL_MINUTES, MIN_POLL_MINUTES,
    PLUGIN_VERSION, STATE_CACHE_FILENAME, DISTANCE_STATE_FILENAME, API_KEY_EXPIRY_WARNING_DAYS,
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

    def _parse_config(self):
        api_key = safe_str(Parameters.get("Mode1", "")).strip()
        vin = safe_str(Parameters.get("Mode2", "")).strip()
        poll = safe_int(Parameters.get("Mode3", DEFAULT_POLL_MINUTES), DEFAULT_POLL_MINUTES)
        poll = clamp(poll or DEFAULT_POLL_MINUTES, MIN_POLL_MINUTES, MAX_POLL_MINUTES)
        if not api_key:
            raise ValueError("API Key is not configured")
        if not vin:
            raise ValueError("VIN is not configured")
        self.poll_minutes = poll
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

    def _api_status_text(self, result):
        code = result.status
        if code is None:
            return "- Connection error"
        meanings = {
            200: "OK", 400: "Bad Request", 401: "Unauthorized / API key expired",
            403: "Forbidden / not authorized", 404: "Not Found", 409: "Conflict",
            422: "Unprocessable / unsupported or disabled", 429: "Too Many Requests / rate limited",
            500: "Internal Server Error", 502: "Bad Gateway", 503: "Service Unavailable",
            504: "Gateway Timeout",
        }
        meaning = meanings.get(code, "HTTP error")
        return "{} {}".format(code, meaning)

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

    def _poll(self):
        now = time.time()
        if now < self.next_retry_at:
            return
        self.last_poll = now
        self.logger.Debug("Polling MySkoda API")
        result = self.api.fetch_vehicle()
        self.api_rate = result.rate_text
        self.rate_remaining = result.rate_remaining_value
        if result.rate_reset_value is not None:
            self.rate_reset_at = now + result.rate_reset_value
        if result.api_key_expires_at:
            self.api_key_expiry = result.api_key_expires_at

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

    def onStart(self):
        try:
            api_key, vin = self._parse_config()
        except ValueError as exc:
            self.logger.Error(str(exc))
            return

        self.logger.Log("Starting MySkoda API Integration {}".format(PLUGIN_VERSION))
        self.devices = DeviceManager(self.logger, Devices)
        self.devices.ensure_devices()
        home = Parameters.get("HomeFolder", ".")
        self.cache_path = os.path.join(home, STATE_CACHE_FILENAME)
        self.distance_path = os.path.join(home, DISTANCE_STATE_FILENAME)
        self._cache_load()
        self._distance_load()
        self.api = MySkodaAPI(api_key, vin, self.logger)
        self._poll()

    def onCommand(self, unit, command, level, hue):
        """Reject local selector changes: these devices are telemetry-only.

        Domoticz selector widgets are inherently interactive. We therefore
        deliberately do not translate selector commands into vehicle/API
        commands. If a dashboard changes a selector locally, restore the
        last API-derived state immediately when possible.
        """
        self.logger.Debug(
            "Ignoring read-only selector command unit={} command={} level={}".format(
                unit, command, level
            )
        )
        if self.devices and self.cached_state is not None:
            try:
                self.devices.restore_selector(unit, self.cached_state)
            except Exception as exc:
                self.logger.Debug("Could not restore selector unit {}: {}".format(unit, exc))

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
