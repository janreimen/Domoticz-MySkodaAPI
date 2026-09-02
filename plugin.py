# -*- coding: utf-8 -*-
"""
<plugin
    key="MySkodaAPI"
    name="MySkoda API Integration"
    author="Jan Reimen"
    version="0.0.1-alpha"
    externallink="https://github.com/janreimen/Domoticz-MySkodaAPI">

    <description>
        MySkoda API Integration for Domoticz.
        Connects to the official Škoda MySkoda Public API
        and exposes vehicle status information to Domoticz.
    </description>

    <params>

        <param field="Username" label="Vehicle VIN" width="350px">
        </param>

        <param field="Password" label="MySkoda API Key" width="350px">
        </param>

        <param field="Mode1" label="Poll interval">
            <options>
                <option label="15 minutes" value="15"/>
                <option label="30 minutes" value="30" default="true"/>
                <option label="60 minutes" value="60"/>
            </options>
        </param>

        <param field="Mode2" label="Debug">
            <options>
                <option label="Normal" value="Normal" default="true"/>
                <option label="Debug" value="Debug"/>
            </options>
        </param>

    </params>
</plugin>
"""
import json
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime

import Domoticz

__version__ = "0.0.1-alpha"
PLUGIN_NAME = "MySkoda API Integration"
API_BASE = "https://public.api.connect.skoda-auto.cz/api/v1"
MIN_POLL_MINUTES = 5
HEARTBEAT_SECONDS = 20

UNITS = {
    "fuel_level": 1,
    "fuel_range": 2,
    "odometer": 3,
    "locked": 4,
    "doors": 5,
    "windows": 6,
    "lights": 7,
    "reachable": 8,
    "motion": 9,
    "climate": 10,
    "ventilation": 11,
    "parking": 12,
    "last_update": 13,
    "key_expiry": 14,
    "api_status": 15,
}

_plugin = None


class BasePlugin:
    def __init__(self):
        self.stop_event = threading.Event()
        self.worker = None
        self.last_success = 0
        self.last_error = ""
        self.rate_limit = {}
        self.key_expiry = ""

    def log(self, message):
        Domoticz.Log("[MySkoda] " + message)

    def error(self, message):
        Domoticz.Error("[MySkoda] " + message)

    def debug(self, message):
        if Parameters.get("Mode3", "False") == "True":
            Domoticz.Debug("[MySkoda] " + message)

    def onStart(self):
        Domoticz.Heartbeat(HEARTBEAT_SECONDS)
        self.create_devices()
        if not Parameters.get("Username", "").strip():
            self.error("Vehicle VIN is not configured.")
        if not Parameters.get("Password", "").strip():
            self.error("MySkoda API key is not configured.")
        self.log("%s %s started" % (PLUGIN_NAME, __version__))
        self.log("Read-only mode: remote vehicle commands are disabled.")
        self.stop_event.clear()
        self.worker = threading.Thread(target=self.poll_loop, name="MySkodaAPI", daemon=True)
        self.worker.start()

    def onStop(self):
        self.stop_event.set()
        if self.worker and self.worker.is_alive():
            self.worker.join(timeout=2)
        self.log("Plugin stopped")

    def onHeartbeat(self):
        if self.last_error and (time.time() - self.last_success) > 300:
            self.update_text(UNITS["api_status"], "ERROR: " + self.last_error)

    def onCommand(self, unit, command, level, color):
        self.log("Ignoring command for Unit %s (%s); write operations are disabled in %s." % (unit, command, __version__))

    def create_device(self, unit, name, device_type=243, subtype=19):
        if unit not in Devices:
            Domoticz.Device(Name=name, Unit=unit, Type=device_type, Subtype=subtype, Used=1).Create()

    def create_devices(self):
        self.create_device(UNITS["fuel_level"], "Fuel level", 243, 6)
        names = {
            "fuel_range": "Fuel range", "odometer": "Odometer", "locked": "Doors locked",
            "doors": "Doors", "windows": "Windows", "lights": "Lights",
            "reachable": "Vehicle reachable", "motion": "Vehicle in motion", "climate": "Climate",
            "ventilation": "Active ventilation", "parking": "Parking position", "last_update": "Last update",
            "key_expiry": "API key expiry", "api_status": "API status",
        }
        for key, name in names.items():
            self.create_device(UNITS[key], name)

    @staticmethod
    def first(obj, *paths):
        for path in paths:
            value = obj
            found = True
            for part in path.split("."):
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    found = False
                    break
            if found and value is not None:
                return value
        return None

    @staticmethod
    def boolean(value):
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        value = str(value).strip().upper()
        if value in ("YES", "TRUE", "ON", "LOCKED", "CLOSED"):
            return True
        if value in ("NO", "FALSE", "OFF", "UNLOCKED", "OPEN"):
            return False
        return None

    @staticmethod
    def number(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def format_number(value):
        number = BasePlugin.number(value)
        if number is None:
            return str(value)
        return str(int(number)) if number.is_integer() else "%.1f" % number

    def api_request(self, vin):
        api_key = Parameters.get("Password", "").strip()
        if not api_key:
            raise RuntimeError("API key is empty")
        request = urllib.request.Request(
            "%s/vehicles/%s" % (API_BASE, vin), method="GET",
            headers={"Accept": "application/json", "X-API-Key": api_key,
                     "User-Agent": "Domoticz-MySkodaAPI/%s" % __version__})
        self.debug("GET %s/vehicles/%s" % (API_BASE, vin))
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8")
                self.rate_limit = {"limit": response.headers.get("RateLimit-Limit"),
                                   "remaining": response.headers.get("RateLimit-Remaining"),
                                   "reset": response.headers.get("RateLimit-Reset")}
                self.key_expiry = response.headers.get("X-API-Key-Expires-At", "")
                return json.loads(body)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                problem = json.loads(body)
            except ValueError:
                problem = {}
            detail = problem.get("detail", "HTTP %s" % exc.code)
            if exc.code == 401:
                raise RuntimeError("API key expired or invalid: %s" % detail)
            if exc.code == 403:
                raise RuntimeError("API key not authorized for this VIN: %s" % detail)
            if exc.code == 422:
                raise RuntimeError("Operation/capability unavailable: %s" % detail)
            if exc.code == 429:
                raise RuntimeError("API rate limit reached; Retry-After=%s" % exc.headers.get("Retry-After", "?"))
            raise RuntimeError("HTTP %s: %s" % (exc.code, detail))
        except urllib.error.URLError as exc:
            raise RuntimeError("Network error: %s" % exc.reason)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Invalid JSON response: %s" % exc)

    def poll_interval_seconds(self):
        try:
            minutes = int(Parameters.get("Mode1", "30"))
        except (TypeError, ValueError):
            minutes = 30
        return max(MIN_POLL_MINUTES, minutes) * 60

    def poll_loop(self):
        while not self.stop_event.is_set():
            try:
                vin = Parameters.get("Username", "").strip()
                if not vin:
                    raise RuntimeError("Vehicle VIN is not configured")
                data = self.api_request(vin)
                self.update_devices(data)
                self.last_success = time.time()
                self.last_error = ""
                self.log("Vehicle state updated")
            except Exception as exc:
                self.last_error = str(exc)
                self.error(str(exc))
                self.update_text(UNITS["api_status"], "ERROR: " + self.last_error)
            self.stop_event.wait(self.poll_interval_seconds())

    def update_text(self, unit, value):
        if unit in Devices:
            Devices[unit].Update(nValue=0, sValue=str(value)[:250])

    def update_boolean_text(self, unit, value, true_text, false_text):
        state = self.boolean(value)
        if state is not None:
            self.update_text(unit, true_text if state else false_text)

    def update_devices(self, response):
        vehicle = response.get("vehicle", response)
        if not isinstance(vehicle, dict):
            raise RuntimeError("API response contains no vehicle object")
        status = vehicle.get("status", {})
        overall = status.get("overall", {}) if isinstance(status, dict) else {}
        fuel = vehicle.get("fuel", vehicle.get("fuelStatus", {}))
        climate = vehicle.get("airConditioning", vehicle.get("airConditioningStatus", {}))
        parking = vehicle.get("parkingPosition", {})
        fuel = fuel if isinstance(fuel, dict) else {}
        climate = climate if isinstance(climate, dict) else {}
        parking = parking if isinstance(parking, dict) else {}

        fuel_level = self.first(fuel, "level", "fuelLevel", "percentage", "remainingPercentage")
        fuel_range = self.first(fuel, "range", "rangeKm", "remainingRange", "combustionRange")
        odometer = self.first(vehicle, "odometer", "mileage", "odometer.value")
        locked = self.first(overall, "doorsLocked", "vehicleLocked", "locked")
        doors = self.first(overall, "doorsOpen", "doors.open")
        windows = self.first(overall, "windowsOpen", "windows.open")
        lights = self.first(overall, "lightsOn", "parkingLightsOn", "lights.on")
        reachable = self.first(overall, "vehicleReachable", "reachable")
        motion = self.first(overall, "vehicleInMotion", "inMotion")
        climate_state = self.first(climate, "status", "state", "active")
        ventilation = self.first(climate, "activeVentilation", "activeVentilation.status", "ventilation", "ventilation.status")
        latitude = self.first(parking, "latitude", "lat")
        longitude = self.first(parking, "longitude", "lon")
        address = self.first(parking, "address", "formattedAddress")

        number = self.number(fuel_level)
        if number is not None and UNITS["fuel_level"] in Devices:
            Devices[UNITS["fuel_level"]].Update(nValue=1, sValue="%.1f" % number)
        if fuel_range is not None:
            self.update_text(UNITS["fuel_range"], "%s km" % self.format_number(fuel_range))
        if odometer is not None:
            self.update_text(UNITS["odometer"], "%s km" % self.format_number(odometer))
        self.update_boolean_text(UNITS["locked"], locked, "Locked", "Unlocked")
        self.update_boolean_text(UNITS["doors"], doors, "Open", "Closed")
        self.update_boolean_text(UNITS["windows"], windows, "Open", "Closed")
        self.update_boolean_text(UNITS["lights"], lights, "ON", "OFF")
        self.update_boolean_text(UNITS["reachable"], reachable, "Reachable", "Not reachable")
        self.update_boolean_text(UNITS["motion"], motion, "Moving", "Parked")
        if climate_state is not None:
            self.update_text(UNITS["climate"], climate_state)
        if ventilation is not None:
            self.update_text(UNITS["ventilation"], ventilation)
        if latitude is not None and longitude is not None:
            position = "GPS %.6f, %.6f" % (float(latitude), float(longitude))
            if address:
                position += " | %s" % address
            self.update_text(UNITS["parking"], position)
        self.update_text(UNITS["last_update"], datetime.now().astimezone().isoformat(timespec="seconds"))
        if self.key_expiry:
            self.update_text(UNITS["key_expiry"], self.key_expiry)

        errors = response.get("errors", [])
        if errors:
            descriptions = []
            for item in errors:
                if isinstance(item, dict):
                    descriptions.append("%s: %s" % (item.get("type", "error"), item.get("detail", "")))
                else:
                    descriptions.append(str(item))
            self.update_text(UNITS["api_status"], "Partial data: " + "; ".join(descriptions))
        else:
            remaining = self.rate_limit.get("remaining")
            suffix = " | quota remaining: %s" % remaining if remaining is not None else ""
            self.update_text(UNITS["api_status"], "OK" + suffix)


def onStart():
    global _plugin
    _plugin = BasePlugin()
    _plugin.onStart()


def onStop():
    if _plugin is not None:
        _plugin.onStop()


def onHeartbeat():
    if _plugin is not None:
        _plugin.onHeartbeat()


def onCommand(Unit, Command, Level, Color):
    if _plugin is not None:
        _plugin.onCommand(Unit, Command, Level, Color)
