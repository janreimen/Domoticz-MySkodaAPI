#!/usr/bin/env python3
"""
<plugin
    key="MySkodaAPI"
    name="MySkoda API Integration"
    author="Jan Reimen"
    version="0.0.2-alpha"
    externallink="https://github.com/janreimen/Domoticz-MySkodaAPI">
    <description>
        MyŠkoda Public API integration for Domoticz.

        Architecture-refactored alpha release. Read-only integration;
        remote vehicle commands are intentionally not implemented yet.
    </description>
    <params>
        <param field="Username" label="Vehicle VIN" width="350px">
            <description>Vehicle VIN</description>
        </param>
        <param field="Password" label="MyŠkoda API Key" password="true" width="350px">
            <description>API key created in the MyŠkoda application</description>
        </param>
        <param field="Mode1" label="Poll interval" width="100px">
            <options>
                <option label="15 minutes" value="15"/>
                <option label="30 minutes" value="30" default="true"/>
                <option label="60 minutes" value="60"/>
            </options>
        </param>
        <param field="Mode2" label="Debug" width="100px">
            <options>
                <option label="Normal" value="0" default="true"/>
                <option label="Debug" value="1"/>
            </options>
        </param>
    </params>
</plugin>
"""

import time
import Domoticz

from constants import PLUGIN_VERSION, DEFAULT_POLL_MINUTES, MIN_POLL_MINUTES, MAX_POLL_MINUTES, UNITS
from devices import DeviceManager
from myskoda_api import MySkodaAPI
from utils import safe_int, iso_to_text
from vehicle import parse_vehicle


class Logger:
    def __init__(self, debug=False):
        self.debug_enabled = debug

    def log(self, message):
        Domoticz.Log("[MySkoda] {}".format(message))

    def debug(self, message):
        if self.debug_enabled:
            Domoticz.Debug("[MySkoda] {}".format(message))

    def error(self, message):
        Domoticz.Error("[MySkoda] {}".format(message))


class BasePlugin:
    def __init__(self):
        self.vin = ""
        self.api_key = ""
        self.poll_minutes = DEFAULT_POLL_MINUTES
        self.debug_enabled = False
        self.last_poll = 0
        self.initialized = False
        self.api = None
        self.devices = None
        self.logger = Logger(False)
        self.api_status = ""

    def onStart(self):
        self.vin = Parameters.get("Username", "").strip().upper()
        self.api_key = Parameters.get("Password", "").strip()
        self.poll_minutes = safe_int(Parameters.get("Mode1", str(DEFAULT_POLL_MINUTES)), DEFAULT_POLL_MINUTES)
        self.poll_minutes = max(MIN_POLL_MINUTES, min(MAX_POLL_MINUTES, self.poll_minutes))
        self.debug_enabled = Parameters.get("Mode2", "0") == "1"
        self.logger = Logger(self.debug_enabled)
        self.logger.log("Starting MyŠkoda API Integration {}".format(PLUGIN_VERSION))

        if not self.vin:
            self.logger.error("Vehicle VIN is not configured")
        if not self.api_key:
            self.logger.error("MyŠkoda API key is not configured")

        self.devices = DeviceManager(self.logger, Devices)
        if len(Devices) == 0:
            self.devices.create_all()
        else:
            self.logger.debug("{} existing MySkoda devices found".format(len(Devices)))

        self.api = MySkodaAPI(self.vin, self.api_key, self.logger)
        self.initialized = True
        if self.vin and self.api_key:
            self.poll()
            self.last_poll = time.time()

    def poll(self):
        self.logger.debug("Starting API poll")
        result = self.api.get_vehicle()
        self.api_status = "HTTP {}".format(result.status) if result.status else (result.error_type or "Error")
        self.devices.update_text("api_status", self.api_status)
        if self.api.rate_limit:
            self.devices.update_text("api_rate_limit", self.api.rate_limit)
        if self.api.api_key_expires:
            self.devices.update_text("api_key_expiry", iso_to_text(self.api.api_key_expires))

        if not result.ok:
            return

        state = parse_vehicle(result.data, self.logger)
        if state is None:
            self.api_status = "Invalid vehicle data"
            self.devices.update_text("api_status", self.api_status)
            self.logger.error("API response does not contain a valid vehicle object")
            return

        self._apply_state(state)
        self.logger.debug("API poll completed successfully")

    def _apply_state(self, state):
        d = self.devices
        d.update_text("vehicle", state.name)
        for key in ("doors_locked", "doors", "windows", "lights", "trunk", "bonnet", "sunroof", "vehicle_state", "air_conditioning", "auxiliary_heating", "active_ventilation"):
            d.update_selector(key, getattr(state, key))
        d.update_percentage("fuel_level", state.fuel_level)
        d.update_distance("fuel_range", state.fuel_range_km)
        d.update_distance("total_range", state.total_range_km)
        d.update_distance("odometer", state.odometer_km)
        d.update_text("parking_address", state.parking_address)
        d.update_text("parking_gps", state.parking_gps)
        d.update_temperature("target_temperature", state.target_temperature)
        d.update_text("vehicle_captured", iso_to_text(state.vehicle_captured))

    def onStop(self):
        self.logger.log("Stopping MyŠkoda API Integration")

    def onHeartbeat(self):
        if not self.initialized or not self.vin or not self.api_key:
            return
        now = time.time()
        if self.last_poll == 0 or now - self.last_poll >= self.poll_minutes * 60:
            self.poll()
            self.last_poll = now

    def onCommand(self, Unit, Command, Level, Color):
        self.logger.debug("Ignoring command for Unit {} (read-only alpha plugin)".format(Unit))


_plugin = BasePlugin()


def onStart():
    _plugin.onStart()


def onStop():
    _plugin.onStop()


def onHeartbeat():
    _plugin.onHeartbeat()


def onCommand(Unit, Command, Level, Color):
    _plugin.onCommand(Unit, Command, Level, Color)
