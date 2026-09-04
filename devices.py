import Domoticz

from constants import UNITS, SELECTORS


class DeviceManager:
    def __init__(self, logger, domoticz_devices):
        self.logger = logger
        self.domoticz_devices = domoticz_devices

    @staticmethod
    def selector_options(level_names):
        return {
            "LevelNames": "|".join(level_names),
            "LevelActions": "|" * (len(level_names) - 1),
            "LevelOffHidden": "false",
            "SelectorStyle": "0",
        }

    def create_all(self):
        self.logger.log("Creating Domoticz devices")
        self.create_text(UNITS["vehicle"], "Vehicle")
        for key, name in [
            ("doors_locked", "Doors Locked"), ("doors", "Doors"),
            ("windows", "Windows"), ("lights", "Lights"),
            ("trunk", "Trunk"), ("bonnet", "Bonnet"), ("sunroof", "Sunroof"),
        ]:
            self.create_selector(UNITS[key], name, SELECTORS[key])
        self.create_percentage(UNITS["fuel_level"], "Fuel Level")
        self.create_distance(UNITS["fuel_range"], "Fuel Range")
        self.create_distance(UNITS["total_range"], "Total Range")
        self.create_distance(UNITS["odometer"], "Odometer")
        self.create_selector(UNITS["vehicle_state"], "Vehicle State", SELECTORS["vehicle_state"])
        self.create_text(UNITS["parking_address"], "Parking Address")
        self.create_text(UNITS["parking_gps"], "Parking GPS")
        self.create_selector(UNITS["air_conditioning"], "Air Conditioning", SELECTORS["air_conditioning"])
        self.create_temperature(UNITS["target_temperature"], "Target Temperature")
        self.create_selector(UNITS["auxiliary_heating"], "Auxiliary Heating", SELECTORS["auxiliary_heating"])
        self.create_selector(UNITS["active_ventilation"], "Active Ventilation", SELECTORS["active_ventilation"])
        for key, name in [
            ("vehicle_captured", "Vehicle Captured"), ("api_key_expiry", "API Key Expiry"),
            ("api_rate_limit", "API Rate Limit"), ("api_status", "API Status"),
        ]:
            self.create_text(UNITS[key], name)

    def create_selector(self, unit, name, levels):
        Domoticz.Device(Name=name, Unit=unit, TypeName="Selector Switch", Options=self.selector_options(levels), Used=1).Create()

    def create_text(self, unit, name):
        Domoticz.Device(Name=name, Unit=unit, TypeName="Text", Used=1).Create()

    def create_percentage(self, unit, name):
        Domoticz.Device(Name=name, Unit=unit, TypeName="Percentage", Used=1).Create()

    def create_distance(self, unit, name):
        Domoticz.Device(Name=name, Unit=unit, Type=243, Subtype=31, Switchtype=0, Options={"Custom": "1;km"}, Used=1).Create()

    def create_temperature(self, unit, name):
        Domoticz.Device(Name=name, Unit=unit, TypeName="Temperature", Used=1).Create()

    def update_selector(self, key, value):
        unit = UNITS[key]
        if unit not in self.domoticz_devices or value is None:
            return
        try:
            level = SELECTORS[key].index(str(value))
        except ValueError:
            self.logger.debug("Unknown selector value '{}' for {}".format(value, key))
            return
        nvalue = level * 10
        self.domoticz_devices[unit].Update(nValue=nvalue, sValue=str(nvalue))

    def update_text(self, key, value):
        unit = UNITS[key]
        if unit in self.domoticz_devices and value is not None:
            self.domoticz_devices[unit].Update(nValue=0, sValue=str(value))

    def update_percentage(self, key, value):
        unit = UNITS[key]
        if unit not in self.domoticz_devices or value is None:
            return
        try:
            value = max(0, min(100, int(value)))
        except (TypeError, ValueError):
            return
        self.domoticz_devices[unit].Update(nValue=value, sValue=str(value))

    def update_distance(self, key, value):
        unit = UNITS[key]
        if unit not in self.domoticz_devices or value is None:
            return
        try:
            value = float(value)
        except (TypeError, ValueError):
            return
        self.domoticz_devices[unit].Update(nValue=0, sValue="{:.1f}".format(value))

    def update_temperature(self, key, value):
        unit = UNITS[key]
        if unit not in self.domoticz_devices or value is None:
            return
        try:
            value = float(value)
        except (TypeError, ValueError):
            return
        self.domoticz_devices[unit].Update(nValue=0, sValue="{:.1f}".format(value))
