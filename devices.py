import Domoticz

from constants import UNITS
from utils import format_coordinate, safe_str


class DeviceManager:
    """Create/update Domoticz devices and expose semantic vehicle states."""

    # State/telemetry devices are deliberately read-only.  Even devices that
    # look like switches are represented as Text so a future command API cannot
    # accidentally be triggered by a dashboard click.
    DEFINITIONS = [
        ("vehicle", "Vehicle", "Text", "text"),
        ("doors_locked", "Doors Locked", "Text", "text"),
        ("doors", "Doors", "Text", "text"),
        ("windows", "Windows", "Text", "text"),
        ("lights", "Lights", "Text", "text"),
        ("trunk", "Trunk", "Text", "text"),
        ("bonnet", "Bonnet", "Text", "text"),
        ("sunroof", "Sunroof", "Text", "text"),
        ("fuel_level", "Fuel Level", "Percentage", "percentage"),
        ("fuel_range", "Fuel Range", "Custom Sensor", "custom_km"),
        ("total_range", "Total Range", "Custom Sensor", "custom_km"),
        ("odometer", "Odometer / Mileage", "Counter", "counter_km"),
        ("vehicle_state", "Vehicle State", "Text", "text"),
        ("parking_address", "Parking Address", "Text", "text"),
        ("parking_gps", "Parking GPS", "Text", "text"),
        ("air_conditioning", "Air Conditioning", "Text", "text"),
        ("target_temperature", "Target Temperature", "Temperature", "temperature"),
        ("auxiliary_heating", "Auxiliary Heating", "Text", "text"),
        ("active_ventilation", "Active Ventilation", "Text", "text"),
        ("vehicle_captured", "Vehicle Captured", "Text", "text"),
        ("api_key_expiry", "API Key Expiry", "Text", "text"),
        ("api_rate_limit", "API Rate Limit", "Text", "text"),
        ("api_status", "API Status", "Text", "text"),
        ("today_distance", "Today Distance", "Counter", "counter_km"),
        ("yesterday_distance", "Yesterday Distance", "Counter", "counter_km"),
        ("vehicle_security", "Vehicle Security", "Text", "text"),
        ("climate_state", "Climate State", "Text", "text"),
        ("data_quality", "Data Quality", "Text", "text"),
    ]

    COUNTER_OPTIONS = {"ValueQuantity": "Distance", "ValueUnits": "km"}
    CUSTOM_KM_OPTIONS = {"Custom": "1;km"}
    CUSTOM_KM_TYPE = 243
    CUSTOM_KM_SUBTYPE = 31
    CUSTOM_KM_SWITCHTYPE = 0

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
        if device is not None:
            try:
                if mode == "custom_km":
                    # Domoticz does not change an existing device's Type/SubType
                    # through Update(). If an earlier plugin version created unit
                    # 10/11 as a generic/unknown device, migrate it explicitly.
                    # Only these plugin-owned units are ever migrated here.
                    if (getattr(device, "Type", None) != self.CUSTOM_KM_TYPE or
                            getattr(device, "SubType", None) != self.CUSTOM_KM_SUBTYPE):
                        self.logger.Log(
                            "Migrating unit {} to Custom Sensor (243/31) with km unit".format(unit)
                        )
                        device.Delete()
                        device = None
                    else:
                        device.Update(
                            nValue=getattr(device, "nValue", 0),
                            sValue=getattr(device, "sValue", "0"),
                            Options=self.CUSTOM_KM_OPTIONS,
                        )
                elif mode == "counter_km":
                    device.Update(
                        nValue=getattr(device, "nValue", 0),
                        sValue=getattr(device, "sValue", "0"),
                        Type=113,
                        SwitchType=3,
                        Options=self.COUNTER_OPTIONS,
                    )
                else:
                    device.Update(
                        nValue=getattr(device, "nValue", 0),
                        sValue=getattr(device, "sValue", ""),
                        TypeName=type_name,
                    )
            except Exception as exc:
                self._log_error("Could not configure unit {}: {}".format(unit, exc))
            return device

        try:
            kwargs = {"Name": name, "Unit": unit, "Used": 1}
            if mode == "custom_km":
                kwargs.update(
                    Type=self.CUSTOM_KM_TYPE,
                    Subtype=self.CUSTOM_KM_SUBTYPE,
                    Switchtype=self.CUSTOM_KM_SWITCHTYPE,
                    Options=self.CUSTOM_KM_OPTIONS,
                )
            elif mode == "counter_km":
                kwargs.update(Type=113, Switchtype=3, Options=self.COUNTER_OPTIONS)
            else:
                kwargs["TypeName"] = type_name
            Domoticz.Device(**kwargs).Create()
        except Exception as exc:
            self._log_error(
                "Failed creating unit {} ({}, {}): {}".format(unit, name, type_name, exc)
            )
            return None
        return self.domoticz_devices.get(unit)

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

    def update(self, state, api_status="OK", api_rate="Unavailable", api_key_expiry="Unknown",
               today_distance=None, yesterday_distance=None, data_quality="GOOD"):
        vehicle = "{}{}".format(
            state.name or "Škoda",
            (" - " + state.license_plate) if state.license_plate else "",
        )
        self.update_text("vehicle", vehicle)
        self.update_text("doors_locked", "LOCKED" if state.doors_locked is True else ("UNLOCKED" if state.doors_locked is False else "UNKNOWN"))
        self.update_text("doors", self._normalized(state.doors))
        self.update_text("lights", self._normalized(state.lights))
        self.update_text("windows", self._normalized(state.windows))
        self.update_text("trunk", self._normalized(state.trunk))
        self.update_text("bonnet", self._normalized(state.bonnet))
        self.update_text("sunroof", self._normalized(state.sunroof))
        self._update_percentage("fuel_level", state.fuel_level)
        self._update_custom_km("fuel_range", state.fuel_range)
        self._update_custom_km("total_range", state.total_range)
        self._update_counter_km("odometer", state.odometer)
        self.update_text("vehicle_state", self._smart_vehicle_state(state))
        self.update_text("parking_address", state.parking_address or "UNKNOWN")
        if state.parking_latitude is not None and state.parking_longitude is not None:
            gps = "{}, {}".format(format_coordinate(state.parking_latitude), format_coordinate(state.parking_longitude))
        else:
            gps = "UNKNOWN"
        self.update_text("parking_gps", gps)
        self.update_text("air_conditioning", self._normalized(state.air_conditioning))
        if state.target_temperature is not None:
            self._update("target_temperature", 0, "{:.1f}".format(float(state.target_temperature)))
        self.update_text("auxiliary_heating", self._normalized(state.auxiliary_heating))
        self.update_text("active_ventilation", self._normalized(state.active_ventilation))
        self.update_text("vehicle_captured", state.captured_at or "UNKNOWN")
        self.update_text("api_key_expiry", api_key_expiry)
        self.update_text("api_rate_limit", api_rate)
        self.update_text("api_status", api_status)
        self._update_counter_km("today_distance", today_distance)
        self._update_counter_km("yesterday_distance", yesterday_distance)
        self.update_text("vehicle_security", self._smart_security(state))
        self.update_text("climate_state", self._smart_climate(state))
        self.update_text("data_quality", data_quality)

    def update_api_only(self, api_status, api_rate, data_quality="UNKNOWN", cached_state=None):
        self.update_text("api_status", api_status)
        self.update_text("api_rate_limit", api_rate)
        self.update_text("data_quality", data_quality)
        if cached_state is not None:
            self.update_text("vehicle_security", self._smart_security(cached_state))
            self.update_text("climate_state", self._smart_climate(cached_state))
            self.update_text("vehicle_state", self._smart_vehicle_state(cached_state))
