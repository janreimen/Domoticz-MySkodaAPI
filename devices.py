import Domoticz

from constants import UNITS
from utils import format_coordinate, safe_str


class DeviceManager:
    """Create/update Domoticz devices and expose semantic vehicle states."""

    # Semantic state devices use native Domoticz selector widgets. They remain
    # telemetry-only: onCommand() explicitly rejects local selector changes.
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
    ]

    COUNTER_OPTIONS = {"ValueQuantity": "Distance", "ValueUnits": "km"}
    CUSTOM_KM_OPTIONS = {"Custom": "1;km"}
    CUSTOM_KM_TYPE = 243
    CUSTOM_KM_SUBTYPE = 31
    CUSTOM_KM_SWITCHTYPE = 0
    CUSTOM_C_OPTIONS = {"Custom": "1;°C"}
    CUSTOM_C_TYPE = 243
    CUSTOM_C_SUBTYPE = 31
    CUSTOM_C_SWITCHTYPE = 0
    CUSTOM_SECONDS_OPTIONS = {"Custom": "1;s"}
    CUSTOM_DAYS_OPTIONS = {"Custom": "1;days"}
    CUSTOM_REQUESTS_OPTIONS = {"Custom": "1;requests"}
    ALERT_TYPE = 243
    ALERT_SUBTYPE = 19
    ALERT_SWITCHTYPE = 0

    SELECTOR_TYPE = 244
    SELECTOR_SUBTYPE = 62
    SELECTOR_SWITCHTYPE = 18
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
        "Unknown": 0, "UNKNOWN": 0,
        "Locked": 10, "LOCKED": 10, "Unlocked": 20, "UNLOCKED": 20,
        "Closed": 10, "CLOSED": 10, "Open": 20, "OPEN": 20,
        "Off": 10, "OFF": 10, "On": 20, "ON": 20,
        "Parked": 10, "PARKED": 10, "Moving": 20, "MOVING": 20, "Other": 30,
        "Secure": 10, "SECURE": 10, "Attention": 20, "ATTENTION": 20,
        "Heating": 20, "HEATING": 20, "Cooling": 30, "COOLING": 30,
        "Ventilation": 40, "VENTILATION": 40, "Climate": 50, "CLIMATE": 50,
        "Charging": 20, "CHARGING": 20, "Not Charging": 10, "NOT_CHARGING": 10,
        "Complete": 30, "COMPLETED": 30, "Scheduled": 40, "SCHEDULED": 40, "Error": 50, "ERROR": 50,
        "Disconnected": 10, "DISCONNECTED": 10, "Connected": 20, "CONNECTED": 20,
        "Immediate": 10, "IMMEDIATE": 10, "Manual": 30, "MANUAL": 30,
    }

    def __init__(self, logger, domoticz_devices):
        self.logger = logger
        self.domoticz_devices = domoticz_devices

    def _log_error(self, message):
        try:
            self.logger.Error(message)
        except Exception:
            pass

    def _create(self, unit, name, type_name, mode):
        device = self.domoticz_devices.get(unit)
        desired = self._desired_definition(mode)

        if device is not None:
            if self._needs_migration(device, desired):
                try:
                    self.logger.Log(
                        "Migrating unit {} ({}) to native {}".format(unit, name, type_name)
                    )
                    device.Delete()
                    device = None
                except Exception as exc:
                    self._log_error("Could not migrate unit {}: {}".format(unit, exc))
                    return device
            else:
                try:
                    # Keep options synchronized without changing the current value.
                    if desired.get("Options"):
                        device.Update(
                            nValue=getattr(device, "nValue", 0),
                            sValue=getattr(device, "sValue", ""),
                            Options=desired["Options"],
                        )
                except Exception as exc:
                    self._log_error("Could not configure unit {}: {}".format(unit, exc))
                return device

        try:
            kwargs = {"Name": name, "Unit": unit, "Used": 1}
            kwargs.update(desired)
            Domoticz.Device(**kwargs).Create()
        except Exception as exc:
            self._log_error(
                "Failed creating unit {} ({}, {}): {}".format(unit, name, type_name, exc)
            )
            return None
        return self.domoticz_devices.get(unit)

    def _desired_definition(self, mode):
        if mode == "custom_km":
            return {"Type": self.CUSTOM_KM_TYPE, "Subtype": self.CUSTOM_KM_SUBTYPE,
                    "Switchtype": self.CUSTOM_KM_SWITCHTYPE, "Options": self.CUSTOM_KM_OPTIONS}
        if mode == "custom_c":
            return {"Type": self.CUSTOM_C_TYPE, "Subtype": self.CUSTOM_C_SUBTYPE,
                    "Switchtype": self.CUSTOM_C_SWITCHTYPE, "Options": self.CUSTOM_C_OPTIONS}
        if mode == "counter_km":
            return {"Type": 113, "Subtype": 0, "Switchtype": 3, "Options": self.COUNTER_OPTIONS}
        if mode == "custom_seconds":
            return {"Type": self.CUSTOM_KM_TYPE, "Subtype": self.CUSTOM_KM_SUBTYPE,
                    "Switchtype": self.CUSTOM_KM_SWITCHTYPE, "Options": self.CUSTOM_SECONDS_OPTIONS}
        if mode == "custom_days":
            return {"Type": self.CUSTOM_KM_TYPE, "Subtype": self.CUSTOM_KM_SUBTYPE,
                    "Switchtype": self.CUSTOM_KM_SWITCHTYPE, "Options": self.CUSTOM_DAYS_OPTIONS}
        if mode == "custom_requests":
            return {"Type": self.CUSTOM_KM_TYPE, "Subtype": self.CUSTOM_KM_SUBTYPE,
                    "Switchtype": self.CUSTOM_KM_SWITCHTYPE, "Options": self.CUSTOM_REQUESTS_OPTIONS}
        if mode == "alert":
            return {"Type": self.ALERT_TYPE, "Subtype": self.ALERT_SUBTYPE,
                    "Switchtype": self.ALERT_SWITCHTYPE}
        if mode.startswith("selector_"):
            return {"Type": self.SELECTOR_TYPE, "Subtype": self.SELECTOR_SUBTYPE,
                    "Switchtype": self.SELECTOR_SWITCHTYPE,
                    "Options": self.SELECTOR_OPTIONS[mode]}
        return {"TypeName": mode}

    @staticmethod
    def _needs_migration(device, desired):
        for attr in ("Type", "Subtype", "SwitchType"):
            key = "Switchtype" if attr == "SwitchType" else attr
            if key in desired and getattr(device, attr, None) != desired[key]:
                return True
        if "TypeName" in desired:
            # Existing text devices created by older versions need no migration.
            return False
        return False

    def ensure_devices(self):
        for key, name, type_name, mode in self.DEFINITIONS:
            self._create(UNITS[key], name, type_name, mode)

    def _update(self, key, nvalue, svalue, **kwargs):
        device = self.domoticz_devices.get(UNITS[key])
        if device is None:
            return
        try:
            device.Update(nvalue, safe_str(svalue), **kwargs)
        except Exception as exc:
            self._log_error("Failed updating {}: {}".format(key, exc))

    def _update_selector(self, key, value):
        device = self.domoticz_devices.get(UNITS[key])
        if device is None:
            return
        text = safe_str(value, "UNKNOWN").strip()
        level = self.SELECTOR_LEVELS.get(text, self.SELECTOR_LEVELS.get(text.upper(), 0))
        self._update(key, level, str(level), Options=self.SELECTOR_OPTIONS[self._selector_mode(key)])

    @staticmethod
    def _selector_mode(key):
        return {
            "doors_locked": "selector_security_lock", "doors": "selector_open_closed",
            "windows": "selector_open_closed", "lights": "selector_on_off",
            "trunk": "selector_open_closed", "bonnet": "selector_open_closed",
            "sunroof": "selector_open_closed", "vehicle_state": "selector_vehicle_state",
            "air_conditioning": "selector_on_off", "auxiliary_heating": "selector_on_off",
            "active_ventilation": "selector_on_off", "vehicle_security": "selector_security",
            "climate_state": "selector_climate", "charging_state": "selector_charging",
            "charging_connected": "selector_connected", "charge_mode": "selector_charge_mode",
        }[key]

    def _update_alert(self, key, level, text):
        device = self.domoticz_devices.get(UNITS[key])
        if device is None:
            return
        try:
            device.Update(int(level), safe_str(text), SuppressTriggers=False)
        except Exception as exc:
            self._log_error("Failed updating {}: {}".format(key, exc))

    def _update_custom_c(self, key, value):
        if value is None:
            return
        number = float(value)
        self._update(key, 0, "{:.1f}".format(number), Options=self.CUSTOM_C_OPTIONS)

    def restore_selector(self, unit, state):
        reverse = {
            UNITS["doors_locked"]: ("doors_locked", "LOCKED" if state.doors_locked is True else ("UNLOCKED" if state.doors_locked is False else "UNKNOWN")),
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
            UNITS["charging_connected"]: ("charging_connected", "CONNECTED" if state.charging_connected else ("DISCONNECTED" if state.charging_connected is False else "UNKNOWN")),
            UNITS["charge_mode"]: ("charge_mode", self._normalized(state.charge_mode)),
        }
        item = reverse.get(unit)
        if item:
            self._update_selector(item[0], item[1])

    def update_text(self, key, text):
        self._update(key, 0, text)

    def _update_percentage(self, key, value):
        if value is None:
            return
        number = max(0.0, min(100.0, float(value)))
        self._update(key, int(round(number)), "{:.1f}".format(number).rstrip("0").rstrip("."))

    @staticmethod
    def _number(value):
        if value is None:
            return 0.0
        return float(value)

    def _update_distance(self, key, value):
        if value is None:
            return
        number = max(0.0, self._number(value))
        self._update(key, 0, "{:.1f}".format(number).rstrip("0").rstrip("."))

    def _update_custom_km(self, key, value):
        if value is None:
            return
        number = max(0.0, self._number(value))
        text = "{:.1f}".format(number).rstrip("0").rstrip(".")
        self._update(key, 0, text, Options=self.CUSTOM_KM_OPTIONS)

    def _update_custom_numeric(self, key, value, options, decimals=0):
        if value is None:
            return
        number = max(0.0, float(value))
        if decimals <= 0:
            text = str(int(round(number)))
        else:
            text = ("{:.%df}" % decimals).format(number).rstrip("0").rstrip(".")
        self._update(key, int(round(number)), text, Options=options)

    def _update_counter_km(self, key, value):
        if value is None:
            return
        number = max(0.0, self._number(value))
        text = "{:.3f}".format(number).rstrip("0").rstrip(".")
        self._update(key, int(round(number)), text, Options=self.COUNTER_OPTIONS)

    @staticmethod
    def _normalized(value):
        return safe_str(value, "UNKNOWN").strip().upper()

    @classmethod
    def _smart_security(cls, state):
        locked = state.doors_locked
        closed_states = [state.doors, state.windows, state.trunk, state.bonnet, state.sunroof]
        known_closed = all(cls._normalized(v) in ("CLOSED", "CLOSE", "NO", "OFF") for v in closed_states)
        any_open = any(cls._normalized(v) in ("OPEN", "YES", "ON") for v in closed_states)
        if locked is True and known_closed:
            return "SECURE"
        if locked is False or any_open:
            return "ATTENTION"
        return "UNKNOWN"

    @classmethod
    def _smart_climate(cls, state):
        heating = cls._normalized(state.auxiliary_heating)
        ventilation = cls._normalized(state.active_ventilation)
        ac = cls._normalized(state.air_conditioning)
        if heating in ("ON", "ACTIVE", "RUNNING"):
            return "HEATING"
        if ventilation in ("ON", "ACTIVE", "RUNNING"):
            return "VENTILATION"
        if ac in ("ON", "ACTIVE", "RUNNING"):
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
        return ",".join(str(x) for x in state.supported_operations)[:250] if state.supported_operations else "NONE"

    def update(self, state, api_status="OK", api_rate="Unavailable", api_key_expiry_days=None,
               vehicle_captured_elapsed=None, api_rate_remaining=None, api_rate_reset=None,
               api_key_status=None, today_distance=None, yesterday_distance=None, data_quality="GOOD"):
        vehicle = "{}{}".format(
            state.name or "Škoda",
            (" - " + state.license_plate) if state.license_plate else "",
        )
        self.update_text("vehicle", vehicle)
        self._update_selector("doors_locked", "LOCKED" if state.doors_locked is True else ("UNLOCKED" if state.doors_locked is False else "UNKNOWN"))
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
            self._update_selector("charging_connected", "CONNECTED" if state.charging_connected else "DISCONNECTED")
        else:
            self.update_text("charging_connected", "UNKNOWN")
        self._update_percentage("charge_target", state.charge_target)
        self._update_selector("charge_mode", self._normalized(state.charge_mode))
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
