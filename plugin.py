#!/usr/bin/env python3

"""
<plugin key="MySkodaAPI" name="MySkoda API Integration" author="Jan Reimen" version="0.0.3-alpha"
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

from constants import (
    DEFAULT_POLL_MINUTES, MAX_POLL_MINUTES, MIN_POLL_MINUTES,
    PLUGIN_VERSION, STATE_CACHE_FILENAME,
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
        self.api_status = "STARTING"
        self.api_rate = "Unavailable"
        self.api_key_expiry = "Unknown"

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

        if not result.ok:
            self._set_failure(result)
            self.logger.Error("MySkoda API: {}".format(result.error))
            if self.devices:
                self.devices.update_api_only(self.api_status, self.api_rate)
            return

        try:
            state = VehicleState.from_api(result.data)
            if not state.vin:
                state.vin = self.api.vin
            self.cached_state = state
            self._cache_save(state)
            self.last_success = now
            self.failure_count = 0
            self.next_retry_at = 0.0
            self.api_status = "OK"
            self.devices.update(state, self.api_status, self.api_rate, self.api_key_expiry)
            self.logger.Log("MySkoda API update successful")
        except Exception as exc:
            self.failure_count += 1
            self.api_status = "INVALID_DATA"
            self.next_retry_at = time.time() + min(self.poll_minutes * 60.0, 3600.0)
            self.logger.Error("Could not parse MySkoda API response: {}".format(exc))
            self.devices.update_api_only(self.api_status, self.api_rate)

    def onStart(self):
        try:
            api_key, vin = self._parse_config()
        except ValueError as exc:
            self.logger.Error(str(exc))
            return

        self.logger.Log("Starting MySkoda API Integration {}".format(PLUGIN_VERSION))
        self.devices = DeviceManager(self.logger, Devices)
        self.devices.ensure_devices()
        self.cache_path = os.path.join(Parameters.get("HomeFolder", "."), STATE_CACHE_FILENAME)
        self._cache_load()
        self.api = MySkodaAPI(api_key, vin, self.logger)
        self._poll()

    def onStop(self):
        self.logger.Log("Stopping MySkoda API Integration")

    def onHeartbeat(self):
        if self.api is None:
            return
        now = time.time()
        if now - self.last_poll >= self.poll_minutes * 60.0:
            self._poll()


_plugin = BasePlugin()


def onStart():
    _plugin.onStart()


def onStop():
    _plugin.onStop()


def onHeartbeat():
    _plugin.onHeartbeat()
