import Domoticz

from constants import UNITS
from utils import format_coordinate, format_number, safe_str


class DeviceManager:
    def __init__(self, logger, domoticz_devices):
        self.logger = logger
        self.domoticz_devices = domoticz_devices

    def _log_error(self, message):
        try:
            self.logger.Error(message)
        except Exception:
            pass

    def _create(self, unit, name, type_, subtype=0, switchtype=0, options=None):
        if unit in self.domoticz_devices:
            return self.domoticz_devices[unit]
        kwargs = {
            "Name": name,
            "Unit": unit,
            "Type": type_,
            "SubType": subtype,
        }
        if switchtype:
            kwargs["Switchtype"] = switchtype
        if options:
            kwargs["Options"] = options
        try:
            Domoticz.Device(**kwargs).Create()
        except Exception as exc:
            self._log_error("Failed creating unit {} ({}): {}".format(unit, name, exc))
            return None
        return self.domoticz_devices.get(unit)

    def ensure_devices(self):
        definitions = [
            ("vehicle", "Vehicle", 243, 19, 0),
            ("doors_locked", "Doors Locked", 244, 62, 0),
            ("doors", "Doors", 243, 19, 0),
            ("windows", "Windows", 243, 19, 0),
            ("lights", "Lights", 243, 19, 0),
            ("trunk", "Trunk", 243, 19, 0),
            ("bonnet", "Bonnet", 243, 19, 0),
            ("sunroof", "Sunroof", 243, 19, 0),
            ("fuel_level", "Fuel Level", 243, 19, 0),
            ("fuel_range", "Fuel Range", 243, 19, 0),
            ("total_range", "Total Range", 243, 19, 0),
            ("odometer", "Odometer", 243, 19, 0),
            ("vehicle_state", "Vehicle State", 243, 19, 0),
            ("parking_address", "Parking Address", 243, 19, 0),
            ("parking_gps", "Parking GPS", 243, 19, 0),
            ("air_conditioning", "Air Conditioning", 243, 19, 0),
            ("target_temperature", "Target Temperature", 80, 5, 0),
            ("auxiliary_heating", "Auxiliary Heating", 243, 19, 0),
            ("active_ventilation", "Active Ventilation", 243, 19, 0),
            ("vehicle_captured", "Vehicle Captured", 243, 19, 0),
            ("api_key_expiry", "API Key Expiry", 243, 19, 0),
            ("api_rate_limit", "API Rate Limit", 243, 19, 0),
            ("api_status", "API Status", 243, 19, 0),
        ]
        for key, name, type_, subtype, switchtype in definitions:
            self._create(UNITS[key], name, type_, subtype, switchtype)

    def update_text(self, key, text):
        device = self.domoticz_devices.get(UNITS[key])
        if device is None:
            return
        try:
            device.Update(0, safe_str(text))
        except Exception as exc:
            self._log_error("Failed updating {}: {}".format(key, exc))

    def update(self, state, api_status="OK", api_rate="Unavailable", api_key_expiry="Unknown"):
        values = {
            "vehicle": "{}{}".format(state.name or "Škoda", (" - " + state.license_plate) if state.license_plate else ""),
            "doors_locked": (1 if state.doors_locked else 0) if state.doors_locked is not None else 0,
            "doors": state.doors,
            "windows": state.windows,
            "lights": state.lights,
            "trunk": state.trunk,
            "bonnet": state.bonnet,
            "sunroof": state.sunroof,
            "fuel_level": format_number(state.fuel_level, 1),
            "fuel_range": format_number(state.fuel_range, 0),
            "total_range": format_number(state.total_range, 0),
            "odometer": format_number(state.odometer, 0),
            "vehicle_state": state.vehicle_state,
            "parking_address": state.parking_address or "Unknown",
            "parking_gps": "{}, {}".format(format_coordinate(state.parking_latitude), format_coordinate(state.parking_longitude)) if state.parking_latitude is not None and state.parking_longitude is not None else "Unknown",
            "air_conditioning": state.air_conditioning,
            "target_temperature": format_number(state.target_temperature, 1),
            "auxiliary_heating": state.auxiliary_heating,
            "active_ventilation": state.active_ventilation,
            "vehicle_captured": state.captured_at or "Unknown",
            "api_key_expiry": api_key_expiry,
            "api_rate_limit": api_rate,
            "api_status": api_status,
        }
        for key, value in values.items():
            self.update_text(key, value)
        device = self.domoticz_devices.get(UNITS["doors_locked"])
        if device is not None and state.doors_locked is not None:
            try:
                device.Update(1 if state.doors_locked else 0, "On" if state.doors_locked else "Off")
            except Exception as exc:
                self._log_error("Failed updating doors_locked: {}".format(exc))

    def update_api_only(self, api_status, api_rate):
        self.update_text("api_status", api_status)
        self.update_text("api_rate_limit", api_rate)
