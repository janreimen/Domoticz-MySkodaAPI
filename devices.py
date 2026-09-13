import Domoticz

from constants import UNITS
from utils import format_coordinate, safe_str


class DeviceManager:
    """Create/update Domoticz devices and expose semantic vehicle states."""

    DEFINITIONS = [
        ("vehicle", "Vehicle", "Text", "text"),
        ("doors_locked", "Doors Locked", "Selector", "selector_security_lock"),
        ("doors", "Doors", "Selector", "selector_open_closed"),
        ("windows", "Windows", "Selector", "selector_open_closed"),
        ("lights", "Lights", "Selector", "selector_on_off"),
        ("trunk", "Trunk", "Selector", "selector_open_closed"),
        ("bonnet", "Bonnet", "Selector", "selector_open_closed"),
        ("sunroof", "Sunroof", "Selector", "selector_open_closed"),
        ("fuel_level", "Fuel Level", "Percentage", "percentage"),
        ("fuel_range", "Fuel Range", "Custom Sensor", "custom_km"),
        ("total_range", "Total Range", "Custom Sensor", "custom_km"),
        ("odometer", "Odometer / Mileage", "Counter", "counter_km"),
        ("vehicle_state", "Vehicle State", "Selector", "selector_vehicle_state"),
        ("parking_address", "Parking Address", "Text", "text"),
        ("parking_gps", "Parking GPS", "Text", "text"),
        ("air_conditioning", "Air Conditioning", "Selector", "selector_on_off"),
        ("target_temperature", "Target Temperature", "Custom Sensor", "custom_c"),
        ("auxiliary_heating", "Auxiliary Heating", "Selector", "selector_on_off"),
        ("active_ventilation", "Active Ventilation", "Selector", "selector_on_off"),
        ("vehicle_captured", "Vehicle Captured", "Custom Sensor", "custom_seconds"),
        ("api_key_expiry", "API Key Expiry", "Custom Sensor", "custom_days"),
        ("api_rate_limit", "API Rate Limit", "Text", "text"),
        ("api_status", "API Status", "Text", "text"),
        ("today_distance", "Today Distance", "Counter", "counter_km"),
        ("yesterday_distance", "Yesterday Distance", "Counter", "counter_km"),
        ("vehicle_security", "Vehicle Security", "Selector", "selector_security"),
        ("climate_state", "Climate State", "Selector", "selector_climate"),
        ("data_quality", "Data Quality", "Text", "text"),
        ("fuel_type", "Fuel / Engine Type", "Text", "text"),
        ("charging_state", "Charging State", "Selector", "selector_charging"),
        ("battery_soc", "Battery SoC", "Percentage", "percentage"),
        ("electric_range", "Electric Range", "Custom Sensor", "custom_km"),
        ("charging_connected", "Charging Connected", "Selector", "selector_connected"),
        ("charge_target", "Charge Target", "Percentage", "percentage"),
        ("charge_mode", "Charge Mode", "Selector", "selector_charge_mode"),
        ("charging_captured", "Charging Captured", "Text", "text"),
        ("fuel_captured", "Fuel Captured", "Text", "text"),
        ("odometer_captured", "Odometer Captured", "Text", "text"),
        ("api_capabilities", "API Capabilities", "Text", "text"),
        ("api_errors", "API Data Errors", "Text", "text"),
        ("supported_operations", "Supported Operations", "Text", "text"),
        ("api_rate_remaining", "API Rate Remaining", "Custom Sensor", "custom_requests"),
        ("api_rate_reset", "API Rate Reset In", "Custom Sensor", "custom_seconds"),
        ("api_key_status", "API Key Status", "Alert", "alert"),
        # New in 0.4.3
        ("charging_power", "Charging Power", "Custom Sensor", "custom_kw"),
        ("remaining_charging_time", "Remaining Charging Time", "Custom Sensor", "custom_minutes"),
        ("charge_type", "Charge Type", "Text", "text"),
    ]

    COUNTER_OPTIONS = {"ValueQuantity": "Distance", "ValueUnits": "km"}
    CUSTOM_KM_OPTIONS = {"Custom": "1;km"}
    CUSTOM_C_OPTIONS = {"Custom": "1;\u00b0C"}
    CUSTOM_SECONDS_OPTIONS = {"Custom": "1;s"}
    CUSTOM_DAYS_OPTIONS = {"Custom": "1;days"}
    CUSTOM_REQUESTS_OPTIONS = {"Custom": "1;requests"}
    CUSTOM_KW_OPTIONS = {"Custom": "1;kW"}
    CUSTOM_MINUTES_OPTIONS = {"Custom": "1;min"}

    CUSTOM_KM_TYPE = CUSTOM_C_TYPE = 243
    CUSTOM_KM_SUBTYPE = CUSTOM_C_SUBTYPE = 31
    CUSTOM_KM_SWITCHTYPE = CUSTOM_C_SWITCHTYPE = 0

    ALERT_TYPE, ALERT_SUBTYPE, ALERT_SWITCHTYPE = 243, 19, 0
    SELECTOR_TYPE, SELECTOR_SUBTYPE, SELECTOR_SWITCHTYPE = 244, 62, 18

    SELECTOR_OPTIONS = {
        "selector_security_lock": {"SelectorStyle": "0", "LevelOffHidden": "false", "LevelNames": "Unknown|Locked|Unlocked"},
        "selector_open_closed": {"SelectorStyle": "0", "LevelOffHidden": "false", "LevelNames": "Unknown|Closed|Open"},
        "selector_on_off": {"SelectorStyle": "0", "LevelOffHidden": "false", "LevelNames": "Unknown|Off|On"},
        "selector_vehicle_state": {"SelectorStyle": "0", "LevelOffHidden": "false", "LevelNames": "Unknown|Parked|Moving|Other"},
        "selector_security": {"SelectorStyle": "0", "LevelOffHidden": "false", "LevelNames": "Unknown|Secure|Attention"},
        "selector_climate": {"SelectorStyle": "0", "LevelOffHidden": "false", "LevelNames": "Unknown|Off|Heating|Cooling|Ventilation|Climate"},
        "selector_charging": {"SelectorStyle": "0", "LevelOffHidden": "false", "LevelNames": "Unknown|Not Charging|Charging|Complete|Scheduled|Error"},
        "selector_connected": {"SelectorStyle": "0", "LevelOffHidden": "false", "LevelNames": "Unknown|Disconnected|Connected"},
        "selector_charge_mode": {"SelectorStyle": "0", "LevelOffHidden": "false", "LevelNames": "Unknown|Immediate|Scheduled|Manual|Other"},
    }

    SELECTOR_LEVELS = {
        "UNKNOWN": 0, "LOCKED": 10, "UNLOCKED": 20, "CLOSED": 10, "OPEN": 20,
        "OFF": 10, "ON": 20, "PARKED": 10, "MOVING": 20, "OTHER": 30,
        "SECURE": 10, "ATTENTION": 20, "HEATING": 20, "COOLING": 30,
        "VENTILATION": 40, "CLIMATE": 50, "CHARGING": 20, "NOT CHARGING": 10,
        "NOT_CHARGING": 10, "COMPLETE": 30, "COMPLETED": 30, "SCHEDULED": 40,
        "ERROR": 50, "DISCONNECTED": 10, "CONNECTED": 20, "IMMEDIATE": 10,
        "MANUAL": 30,
    }

    _SELECTOR_MODE_BY_KEY = {k: m for k, _n, _t, m in DEFINITIONS if m.startswith("selector_")}

    def __init__(self, logger, domoticz_devices):
        self.logger = logger
        self.domoticz_devices = domoticz_devices

    def _log_error(self, message):
        try:
            self.logger.Error(message)
        except Exception:
            pass

    # ---- creation / migration -------------------------------------------

    def ensure_devices(self):
        for key, name, type_name, mode in self.DEFINITIONS:
            self._create(UNITS[key], name, type_name, mode)

    def _create(self, unit, name, type_name, mode):
        device = self.domoticz_devices.get(unit)
        desired = self._desired_definition(mode)

        if device is not None:
            if self._needs_migration(device, desired):
                if not self._migrate_in_place(unit, name, type_name, device, desired):
                    return device
            else:
                self._synchronize_options(unit, device, desired)
            return device

        try:
            Domoticz.Device(Name=name, Unit=unit, Used=1, **desired).Create()
        except Exception as exc:
            self._log_error("Failed creating unit {} ({}, {}): {}".format(unit, name, type_name, exc))
            return None
        return self.domoticz_devices.get(unit)

    def _synchronize_options(self, unit, device, desired):
        if not desired.get("Options"):
            return
        try:
            device.Update(nValue=getattr(device, "nValue", 0), sValue=getattr(device, "sValue", ""), Options=desired["Options"])
        except Exception as exc:
            self._log_error("Could not configure unit {}: {}".format(unit, exc))

    def _migrate_in_place(self, unit, name, type_name, device, desired):
        try:
            self.logger.Log("Migrating unit {} ({}) to native {} in-place".format(unit, name, type_name))
            kwargs = {"Type": desired["Type"], "SubType": desired["Subtype"], "SwitchType": desired["Switchtype"], "SuppressTriggers": True}
            if desired.get("Options"):
                kwargs["Options"] = desired["Options"]
            device.Update(nValue=getattr(device, "nValue", 0), sValue=getattr(device, "sValue", ""), **kwargs)
            return True
        except Exception as exc:
            self._log_error("Could not migrate unit {} ({}) in-place: {}".format(unit, name, exc))
            return False

    def _desired_definition(self, mode):
        if mode == "custom_km":
            return {"Type": self.CUSTOM_KM_TYPE, "Subtype": self.CUSTOM_KM_SUBTYPE, "Switchtype": self.CUSTOM_KM_SWITCHTYPE, "Options": self.CUSTOM_KM_OPTIONS}
        if mode == "custom_c":
            return {"Type": self.CUSTOM_C_TYPE, "Subtype": self.CUSTOM_C_SUBTYPE, "Switchtype": self.CUSTOM_C_SWITCHTYPE, "Options": self.CUSTOM_C_OPTIONS}
        if mode == "counter_km":
            return {"Type": 113, "Subtype": 0, "Switchtype": 3, "Options": self.COUNTER_OPTIONS}
        if mode == "custom_seconds":
            return {"Type": self.CUSTOM_KM_TYPE, "Subtype": self.CUSTOM_KM_SUBTYPE, "Switchtype": self.CUSTOM_KM_SWITCHTYPE, "Options": self.CUSTOM_SECONDS_OPTIONS}
        if mode == "custom_days":
            return {"Type": self.CUSTOM_KM_TYPE, "Subtype": self.CUSTOM_KM_SUBTYPE, "Switchtype": self.CUSTOM_KM_SWITCHTYPE, "Options": self.CUSTOM_DAYS_OPTIONS}
        if mode == "custom_requests":
            return {"Type": self.CUSTOM_KM_TYPE, "Subtype": self.CUSTOM_KM_SUBTYPE, "Switchtype": self.CUSTOM_KM_SWITCHTYPE, "Options": self.CUSTOM_REQUESTS_OPTIONS}
        if mode == "custom_kw":
            return {"Type": self.CUSTOM_KM_TYPE, "Subtype": self.CUSTOM_KM_SUBTYPE, "Switchtype": self.CUSTOM_KM_SWITCHTYPE, "Options": self.CUSTOM_KW_OPTIONS}
        if mode == "custom_minutes":
            return {"Type": self.CUSTOM_KM_TYPE, "Subtype": self.CUSTOM_KM_SUBTYPE, "Switchtype": self.CUSTOM_KM_SWITCHTYPE, "Options": self.CUSTOM_MINUTES_OPTIONS}
        if mode == "alert":
            return {"Type": self.ALERT_TYPE, "Subtype": self.ALERT_SUBTYPE, "Switchtype": self.ALERT_SWITCHTYPE}
        if mode.startswith("selector_"):
            return {"Type": self.SELECTOR_TYPE, "Subtype": self.SELECTOR_SUBTYPE, "Switchtype": self.SELECTOR_SWITCHTYPE, "Options": self.SELECTOR_OPTIONS[mode]}
        return {"TypeName": mode}

    @staticmethod
    def _needs_migration(device, desired):
        checks = (("Type", "Type"), ("SubType", "Subtype"), ("SwitchType", "Switchtype"))
        for device_attr, desired_key in checks:
            if desired_key in desired and getattr(device, device_attr, None) != desired[desired_key]:
                return True
        return False

    # ---- writes -----------------------------------------------------------

    def _update(self, key, nvalue, svalue, **kwargs):
        device = self.domoticz_devices.get(UNITS[key])
        if device is None:
            return
        try:
            device.Update(nvalue, safe_str(svalue), **kwargs)
        except Exception as exc:
            self._log_error("Failed updating {}: {}".format(key, exc))

    def update_text(self, key, text):
        self._update(key, 0, text)

    @staticmethod
    def _format_number(number, decimals):
        if decimals <= 0:
            return str(int(round(number)))
        return ("{:.%df}" % decimals).format(number).rstrip("0").rstrip(".")

    def _update_percentage(self, key, value):
        if value is None:
            return
        number = max(0.0, min(100.0, float(value)))
        self._update(key, int(round(number)), self._format_number(number, 1))

    def _update_custom_km(self, key, value):
        if value is None:
            return
        number = max(0.0, float(value))
        self._update(key, 0, self._format_number(number, 1), Options=self.CUSTOM_KM_OPTIONS)

    def _update_custom_c(self, key, value):
        if value is None:
            return
        self._update(key, 0, "{:.1f}".format(float(value)), Options=self.CUSTOM_C_OPTIONS)

    def _update_counter_km(self, key, value):
        if value is None:
            return
        number = max(0.0, float(value))
        self._update(key, int(round(number)), self._format_number(number, 3), Options=self.COUNTER_OPTIONS)

    def _update_custom_numeric(self, key, value, options, decimals=0):
        if value is None:
            return
        number = max(0.0, float(value))
        self._update(key, int(round(number)), self._format_number(number, decimals), Options=options)

    def _update_alert(self, key, level, text):
        device = self.domoticz_devices.get(UNITS[key])
        if device is None:
            return
        try:
            device.Update(int(level), safe_str(text), SuppressTriggers=False)
        except Exception as exc:
            self._log_error("Failed updating {}: {}".format(key, exc))

    # ---- selectors ----------------------------------------------------------

    @staticmethod
    def _normalized(value):
        return safe_str(value, "UNKNOWN").strip().upper()

    def _update_selector(self, key, value):
        mode = self._SELECTOR_MODE_BY_KEY[key]
        level = self.SELECTOR_LEVELS.get(safe_str(value, "UNKNOWN").strip().upper(), 0)
        self._update(key, level, str(level), Options=self.SELECTOR_OPTIONS[mode])

    @staticmethod
    def _locked_text(locked):
        return "LOCKED" if locked is True else ("UNLOCKED" if locked is False else "UNKNOWN")

    @staticmethod
    def _connected_text(connected):
        return "CONNECTED" if connected is True else ("DISCONNECTED" if connected is False else "UNKNOWN")

    def restore_selector(self, unit, state):
        by_unit = {
            UNITS["doors_locked"]: ("doors_locked", self._locked_text(state.doors_locked)),
            UNITS["doors"]: ("doors", self._normalized(state.doors)),
            UNITS["windows"]: ("windows", self._normalized(state.windows)),
            UNITS["lights"]: ("lights", self._normalized(state.lights)),
            UNITS["trunk"]: ("trunk", self._normalized(state.trunk)),
            UNITS["bonnet"]: ("bonnet", self._normalized(state.bonnet)),
            UNITS["sunroof"]: ("sunroof", self._normalized(state.sunroof)),
            UNITS["vehicle_state"]: ("vehicle_state", self._smart_vehicle_state(state)),
            UNITS["air_conditioning"]: ("air_conditioning", self._normalized(state.air_conditioning)),
            UNITS["auxiliary_heating"]: ("auxiliary_heating", self._normalized(state.auxiliary_heating)),
            UNITS["active_ventilation"]: ("active_ventilation", self._normalized(state.active_ventilation)),
            UNITS["vehicle_security"]: ("vehicle_security", self._smart_security(state)),
            UNITS["climate_state"]: ("climate_state", self._smart_climate(state)),
            UNITS["charging_state"]: ("charging_state", self._normalized(state.charging_state)),
            UNITS["charging_connected"]: ("charging_connected", self._connected_text(state.charging_connected)),
            UNITS["charge_mode"]: ("charge_mode", self._normalized(state.charge_mode)),
        }
        item = by_unit.get(unit)
        if item:
            self._update_selector(*item)

    # ---- derived states -----------------------------------------------------

    @classmethod
    def _smart_security(cls, state):
        closed_states = [state.doors, state.windows, state.trunk, state.bonnet, state.sunroof]
        known_closed = all(cls._normalized(v) in ("CLOSED", "CLOSE", "NO", "OFF") for v in closed_states)
        any_open = any(cls._normalized(v) in ("OPEN", "YES", "ON") for v in closed_states)
        if state.doors_locked is True and known_closed:
            return "SECURE"
        if state.doors_locked is False or any_open:
            return "ATTENTION"
        return "UNKNOWN"

    @classmethod
    def _smart_climate(cls, state):
        heating = cls._normalized(state.auxiliary_heating)
        ventilation = cls._normalized(state.active_ventilation)
        ac = cls._normalized(state.air_conditioning)
        active = ("ON", "ACTIVE", "RUNNING")
        if heating in active:
            return "HEATING"
        if ventilation in active:
            return "VENTILATION"
        if ac in active:
            return "CLIMATE"
        if heating == ventilation == ac == "OFF":
            return "OFF"
        return "UNKNOWN"

    @classmethod
    def _smart_vehicle_state(cls, state):
        parking = cls._normalized(state.parking_state)
        vehicle = cls._normalized(state.vehicle_state)
        if parking == "PARKED" or vehicle == "PARKED":
            return "PARKED"
        if vehicle in ("MOVING", "DRIVING", "IN_MOTION"):
            return "MOVING"
        if vehicle not in ("UNKNOWN", ""):
            return vehicle
        return "UNKNOWN"

    @staticmethod
    def _capabilities(state):
        caps = []
        if state.fuel_type not in ("UNKNOWN", ""):
            caps.append("FUEL")
        if state.battery_soc is not None or state.charging_state not in ("UNKNOWN", ""):
            caps.append("CHARGING")
        if state.air_conditioning not in ("UNKNOWN", ""):
            caps.append("CLIMATE")
        if state.auxiliary_heating not in ("UNKNOWN", ""):
            caps.append("AUX_HEATING")
        if state.active_ventilation not in ("UNKNOWN", ""):
            caps.append("VENTILATION")
        return ",".join(caps) if caps else "UNKNOWN"

    @staticmethod
    def _api_errors(state):
        if not state.api_errors:
            return "NONE"
        values = []
        for item in state.api_errors:
            if isinstance(item, dict):
                code = item.get("type") or item.get("code") or item.get("title") or "UNKNOWN"
                values.append(str(code).split("/")[-1])
            else:
                values.append(str(item))
        return ",".join(values)[:250]

    @staticmethod
    def _operations(state):
        if not state.supported_operations:
            return "NONE"
        return ",".join(str(x) for x in state.supported_operations)[:250]

    # ---- full update ----------------------------------------------------------

    def update(self, state, api_status="OK", api_rate="Unavailable", api_key_expiry_days=None,
               vehicle_captured_elapsed=None, api_rate_remaining=None, api_rate_reset=None,
               api_key_status=None, today_distance=None, yesterday_distance=None, data_quality="GOOD"):
        vehicle = "{}{}".format(state.name or "\u0160koda", " - " + state.license_plate if state.license_plate else "")
        self.update_text("vehicle", vehicle)

        self._update_selector("doors_locked", self._locked_text(state.doors_locked))
        self._update_selector("doors", self._normalized(state.doors))
        self._update_selector("lights", self._normalized(state.lights))
        self._update_selector("windows", self._normalized(state.windows))
        self._update_selector("trunk", self._normalized(state.trunk))
        self._update_selector("bonnet", self._normalized(state.bonnet))
        self._update_selector("sunroof", self._normalized(state.sunroof))

        self._update_percentage("fuel_level", state.fuel_level)
        self._update_custom_km("fuel_range", state.fuel_range)
        self._update_custom_km("total_range", state.total_range)
        self._update_counter_km("odometer", state.odometer)
        self._update_selector("vehicle_state", self._smart_vehicle_state(state))

        self.update_text("parking_address", state.parking_address or "UNKNOWN")
        if state.parking_latitude is not None and state.parking_longitude is not None:
            gps = "{}, {}".format(format_coordinate(state.parking_latitude), format_coordinate(state.parking_longitude))
        else:
            gps = "UNKNOWN"
        self.update_text("parking_gps", gps)

        self._update_selector("air_conditioning", self._normalized(state.air_conditioning))
        if state.target_temperature is not None:
            self._update_custom_c("target_temperature", state.target_temperature)
        self._update_selector("auxiliary_heating", self._normalized(state.auxiliary_heating))
        self._update_selector("active_ventilation", self._normalized(state.active_ventilation))

        self._update_custom_numeric("vehicle_captured", vehicle_captured_elapsed, self.CUSTOM_SECONDS_OPTIONS)
        self._update_custom_numeric("api_key_expiry", api_key_expiry_days, self.CUSTOM_DAYS_OPTIONS, decimals=2)
        if api_key_status:
            self._update_alert("api_key_status", api_key_status["level"], api_key_status["text"])
        self.update_text("api_rate_limit", api_rate)
        self._update_custom_numeric("api_rate_remaining", api_rate_remaining, self.CUSTOM_REQUESTS_OPTIONS)
        self._update_custom_numeric("api_rate_reset", api_rate_reset, self.CUSTOM_SECONDS_OPTIONS)
        self.update_text("api_status", api_status)

        self._update_counter_km("today_distance", today_distance)
        self._update_counter_km("yesterday_distance", yesterday_distance)

        self._update_selector("vehicle_security", self._smart_security(state))
        self._update_selector("climate_state", self._smart_climate(state))
        self.update_text("data_quality", data_quality)
        self.update_text("fuel_type", self._normalized(state.fuel_type))

        self._update_selector("charging_state", self._normalized(state.charging_state))
        self._update_percentage("battery_soc", state.battery_soc)
        self._update_custom_km("electric_range", state.electric_range)
        if state.charging_connected is not None:
            self._update_selector("charging_connected", self._connected_text(state.charging_connected))
        else:
            self.update_text("charging_connected", "UNKNOWN")
        self._update_percentage("charge_target", state.charge_target)
        self._update_selector("charge_mode", self._normalized(state.charge_mode))
        self._update_custom_numeric("charging_power", state.charging_power, self.CUSTOM_KW_OPTIONS, decimals=1)
        self._update_custom_numeric("remaining_charging_time", state.remaining_charging_time, self.CUSTOM_MINUTES_OPTIONS)
        self.update_text("charge_type", self._normalized(state.charge_type))
        self.update_text("charging_captured", state.charging_captured_at or "UNKNOWN")
        self.update_text("fuel_captured", state.fuel_captured_at or "UNKNOWN")
        self.update_text("odometer_captured", state.odometer_captured_at or "UNKNOWN")

        self.update_text("api_capabilities", self._capabilities(state))
        self.update_text("api_errors", self._api_errors(state))
        self.update_text("supported_operations", self._operations(state))

    def update_api_only(self, api_status, api_rate, data_quality="UNKNOWN", cached_state=None,
                         api_rate_remaining=None, api_rate_reset=None, api_key_status=None):
        self.update_text("api_status", api_status)
        self.update_text("api_rate_limit", api_rate)
        if api_key_status:
            self._update_alert("api_key_status", api_key_status["level"], api_key_status["text"])
        self._update_custom_numeric("api_rate_remaining", api_rate_remaining, self.CUSTOM_REQUESTS_OPTIONS)
        self._update_custom_numeric("api_rate_reset", api_rate_reset, self.CUSTOM_SECONDS_OPTIONS)
        self.update_text("data_quality", data_quality)
        if cached_state is not None:
            self.update_text("vehicle_security", self._smart_security(cached_state))
            self.update_text("climate_state", self._smart_climate(cached_state))
            self.update_text("vehicle_state", self._smart_vehicle_state(cached_state))
