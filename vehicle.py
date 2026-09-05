from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional

from utils import safe_float, safe_str


TRUE_VALUES = {True, 1, "1", "true", "True", "TRUE", "yes", "on", "locked", "closed"}
FALSE_VALUES = {False, 0, "0", "false", "False", "FALSE", "no", "off", "unlocked", "open"}


def first(data, *paths, default=None):
    for path in paths:
        current = data
        try:
            for part in path.split("."):
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    current = None
                if current is None:
                    break
            if current is not None:
                return current
        except Exception:
            continue
    return default


def boolish(value, default=None):
    if value in TRUE_VALUES:
        return True
    if value in FALSE_VALUES:
        return False
    if isinstance(value, str):
        lower = value.strip().lower()
        if lower in {"true", "1", "yes", "on", "locked", "closed", "active", "available", "yes"}:
            return True
        if lower in {"false", "0", "no", "off", "unlocked", "open", "inactive", "unavailable"}:
            return False
    return default


def state_text(value, default="Unknown"):
    if value is None:
        return default
    if isinstance(value, bool):
        return "ON" if value else "OFF"
    if isinstance(value, dict):
        nested = first(value, "state", "status", default=None)
        if nested is not None:
            return state_text(nested, default)
    return safe_str(value, default)


def number_from(value, *keys):
    if isinstance(value, dict):
        return safe_float(first(value, *keys, default=None))
    return safe_float(value)


@dataclass
class VehicleState:
    vin: str = ""
    name: str = ""
    license_plate: str = ""
    doors_locked: Optional[bool] = None
    doors: str = "Unknown"
    windows: str = "Unknown"
    lights: str = "Unknown"
    trunk: str = "Unknown"
    bonnet: str = "Unknown"
    sunroof: str = "Unknown"
    fuel_level: Optional[float] = None
    fuel_range: Optional[float] = None
    total_range: Optional[float] = None
    odometer: Optional[float] = None
    vehicle_state: str = "Unknown"
    parking_state: str = "Unknown"
    parking_address: str = ""
    parking_latitude: Optional[float] = None
    parking_longitude: Optional[float] = None
    air_conditioning: str = "Unknown"
    target_temperature: Optional[float] = None
    auxiliary_heating: str = "Unknown"
    active_ventilation: str = "Unknown"
    fuel_type: str = "Unknown"
    charging_state: str = "Unknown"
    battery_soc: Optional[float] = None
    electric_range: Optional[float] = None
    charging_connected: Optional[bool] = None
    charge_target: Optional[float] = None
    charge_mode: str = "Unknown"
    charging_captured_at: str = ""
    fuel_captured_at: str = ""
    odometer_captured_at: str = ""
    api_errors: list = field(default_factory=list)
    supported_operations: list = field(default_factory=list)
    captured_at: str = ""
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    def to_dict(self):
        result = asdict(self)
        result.pop("raw", None)
        return result

    @classmethod
    def from_api(cls, data):
        # Current API response wraps all vehicle fields below "vehicle".
        root = data.get("vehicle") if isinstance(data, dict) else None
        if not isinstance(root, dict):
            root = data if isinstance(data, dict) else {}

        info = root.get("info") or {}
        status = root.get("status") or {}
        overall = status.get("overall") or {}
        detail = status.get("detail") or {}
        fuel = root.get("fuelStatus") or root.get("fuel_status") or {}
        primary = fuel.get("primaryEngineRange") or {}
        odo = root.get("odometer") or {}
        parking = root.get("parkingPosition") or root.get("parking_position") or {}
        gps = parking.get("gpsCoordinates") or parking.get("gps_coordinates") or {}
        ac = root.get("airConditioning") or root.get("air_conditioning") or {}
        heat = root.get("auxiliaryHeating") or root.get("auxiliary_heating") or {}
        vent = root.get("activeVentilation") or root.get("active_ventilation") or {}
        charging = root.get("charging") or {}
        errors = data.get("errors") if isinstance(data, dict) else []
        operations = root.get("operations") or []
        if not isinstance(errors, list):
            errors = []

        vin = safe_str(first(root, "vin", default=first(info, "vin", "vehicleIdentificationNumber", default="")))
        name = safe_str(first(root, "name", default=first(info, "name", "vehicleName", "nickname", default="")))
        plate = safe_str(first(root, "licensePlate", "license_plate", default=first(info, "licensePlate", "license_plate", "registrationNumber", default="")))

        locked = boolish(first(overall, "doorsLocked", "reliableLockStatus", "locked", default=first(status, "doorsLocked", "reliableLockStatus", "locked", default=None)))
        doors = first(overall, "doors", "doorState", "doorStatus", default=first(status, "doors", "doorState", "doorStatus", default="Unknown"))
        windows = first(overall, "windows", "windowState", "windowStatus", default=first(status, "windows", "windowState", "windowStatus", default="Unknown"))
        lights = first(overall, "lights", "lightState", "lightStatus", default=first(status, "lights", "lightState", "lightStatus", default="Unknown"))
        trunk = first(detail, "trunk", "trunkState", "trunkStatus", default=first(status, "trunk", "trunkState", "trunkStatus", default="Unknown"))
        bonnet = first(detail, "bonnet", "hood", "bonnetState", "bonnetStatus", default=first(status, "bonnet", "hood", "bonnetState", "bonnetStatus", default="Unknown"))
        sunroof = first(detail, "sunroof", "sunroofState", "sunroofStatus", default=first(status, "sunroof", "sunroofState", "sunroofStatus", default="Unknown"))

        fuel_level = safe_float(first(primary, "currentFuelLevelInPercent", default=first(fuel, "currentFuelLevel", "fuelLevel", "level", "fuelLevelPercent", default=None)))
        fuel_type = safe_str(first(primary, "engineType", default=first(fuel, "carType", "engineType", default="Unknown")))
        fuel_range = safe_float(first(primary, "remainingRangeInKm", default=first(fuel, "fuelRange", "range", "remainingRange", default=None)))
        total_range = safe_float(first(fuel, "totalRangeInKm", "totalRange", default=first(root, "totalRangeInKm", "totalRange", default=None)))
        odometer = safe_float(first(odo, "mileageInKm", "value", "distance", "odometer", default=first(root, "odometer", default=None)))

        vehicle_state = state_text(first(root, "state", default=first(overall, "vehicleState", default="Unknown")))
        parking_state = state_text(first(parking, "state", "parkingState", default="Unknown"))
        address = first(parking, "formattedAddress", "address", "location.address", default="")
        latitude = safe_float(first(gps, "latitude", "lat", default=first(parking, "latitude", "lat", default=None)))
        longitude = safe_float(first(gps, "longitude", "lon", "lng", default=first(parking, "longitude", "lon", "lng", default=None)))

        ac_state = state_text(first(ac, "state", "status", "active", default="Unknown"))
        target = first(ac, "targetTemperature", "targetTemperatureCelsius", "temperature", default=first(heat, "targetTemperature", "targetTemperatureCelsius", "temperature", default=None))
        target_temp = number_from(target, "value", "celsius", "temperature")
        heat_state = state_text(first(heat, "state", "status", "active", default="Unknown"))
        vent_state = state_text(first(vent, "state", "status", "active", default="Unknown"))
        captured = safe_str(first(status, "carCapturedTimestamp", default=first(root, "carCapturedTimestamp", default=first(odo, "carCapturedTimestamp", default=""))))
        fuel_captured = safe_str(first(primary, "carCapturedTimestamp", default=first(fuel, "carCapturedTimestamp", default="")))
        odo_captured = safe_str(first(odo, "carCapturedTimestamp", default=""))

        charging_state = state_text(first(charging, "state", "status", "chargingState", default="Unknown"))
        battery_soc = safe_float(first(charging, "batteryLevelInPercent", "stateOfChargeInPercent", "currentSoCInPercent", "socInPercent", default=first(charging, "battery", "soc", default=None)))
        electric_range = safe_float(first(charging, "remainingRangeInKm", "electricRangeInKm", "rangeInKm", default=None))
        charging_connected = boolish(first(charging, "connected", "isConnected", "pluggedIn", "chargingCableConnected", default=None))
        charge_target = safe_float(first(charging, "targetStateOfChargeInPercent", "targetSoCInPercent", "targetBatteryLevelInPercent", "targetSoc", default=None))
        charge_mode = state_text(first(charging, "mode", "chargeMode", "chargingMode", default="Unknown"))
        charging_captured = safe_str(first(charging, "carCapturedTimestamp", "capturedAt", default=""))

        return cls(
            vin=vin, name=name, license_plate=plate,
            doors_locked=locked, doors=state_text(doors), windows=state_text(windows),
            lights=state_text(lights), trunk=state_text(trunk), bonnet=state_text(bonnet),
            sunroof=state_text(sunroof), fuel_level=fuel_level, fuel_range=fuel_range,
            total_range=total_range, odometer=odometer, vehicle_state=vehicle_state,
            parking_state=parking_state, parking_address=safe_str(address),
            parking_latitude=latitude, parking_longitude=longitude,
            air_conditioning=ac_state, target_temperature=target_temp,
            auxiliary_heating=heat_state, active_ventilation=vent_state,
            fuel_type=fuel_type, charging_state=charging_state, battery_soc=battery_soc,
            electric_range=electric_range, charging_connected=charging_connected,
            charge_target=charge_target, charge_mode=charge_mode,
            charging_captured_at=charging_captured, fuel_captured_at=fuel_captured,
            odometer_captured_at=odo_captured, api_errors=errors,
            supported_operations=[(x.get("name") if isinstance(x, dict) else str(x)) for x in operations],
            captured_at=captured, raw=data,
        )

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            return cls()
        allowed = {k: v for k, v in data.items() if k in cls.__dataclass_fields__ and k != "raw"}
        return cls(**allowed)
