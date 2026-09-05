from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional

from utils import safe_float, safe_int, safe_str


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
        if lower in {"true", "1", "yes", "on", "locked", "closed", "active", "available"}:
            return True
        if lower in {"false", "0", "no", "off", "unlocked", "open", "inactive", "unavailable"}:
            return False
    return default


def state_text(value, default="Unknown"):
    if value is None:
        return default
    if isinstance(value, bool):
        return "ON" if value else "OFF"
    return safe_str(value, default)


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
    captured_at: str = ""
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    def to_dict(self):
        result = asdict(self)
        result.pop("raw", None)
        return result

    @classmethod
    def from_api(cls, data):
        data = data if isinstance(data, dict) else {}
        info = data.get("info") or {}
        status = data.get("status") or {}
        fuel = data.get("fuelStatus") or data.get("fuel_status") or {}
        odo = data.get("odometer") or {}
        parking = data.get("parkingPosition") or data.get("parking_position") or {}
        ac = data.get("airConditioning") or data.get("air_conditioning") or {}
        heat = data.get("auxiliaryHeating") or data.get("auxiliary_heating") or {}
        vent = data.get("activeVentilation") or data.get("active_ventilation") or {}

        vin = safe_str(first(info, "vin", "vehicleIdentificationNumber", default=first(data, "vin", default="")))
        name = safe_str(first(info, "name", "vehicleName", "nickname", default=first(data, "name", default="")))
        plate = safe_str(first(info, "licensePlate", "license_plate", "registrationNumber", default=""))

        locked = boolish(first(status, "doorsLocked", "doorLockState", "locked", default=None))
        doors = first(status, "doors", "doorState", "doorStatus", default="Unknown")
        windows = first(status, "windows", "windowState", "windowStatus", default="Unknown")
        lights = first(status, "lights", "lightState", "lightStatus", default="Unknown")
        trunk = first(status, "trunk", "trunkState", "trunkStatus", default="Unknown")
        bonnet = first(status, "bonnet", "hood", "bonnetState", "bonnetStatus", default="Unknown")
        sunroof = first(status, "sunroof", "sunroofState", "sunroofStatus", default="Unknown")

        fuel_level = safe_float(first(fuel, "currentFuelLevel", "fuelLevel", "level", "fuelLevelPercent", default=None))
        fuel_range = safe_float(first(fuel, "fuelRange", "range", "remainingRange", default=None))
        total_range = safe_float(first(status, "totalRange", "range", default=first(fuel, "totalRange", default=None)))
        odometer = safe_float(first(odo, "value", "distance", "odometer", default=first(data, "odometer", default=None)))

        vehicle_state = state_text(first(status, "vehicleState", "state", "ignitionState", default="Unknown"))
        parking_state = state_text(first(parking, "state", "parkingState", default="Unknown"))
        address = first(parking, "address", "formattedAddress", "location.address", default="")
        latitude = safe_float(first(parking, "latitude", "lat", "coordinates.latitude", "location.latitude", default=None))
        longitude = safe_float(first(parking, "longitude", "lon", "lng", "coordinates.longitude", "location.longitude", default=None))

        ac_state = state_text(first(ac, "state", "status", "active", default="Unknown"))
        target_temp = safe_float(first(ac, "targetTemperature", "targetTemperatureCelsius", "temperature", default=None))
        heat_state = state_text(first(heat, "state", "status", "active", default="Unknown"))
        vent_state = state_text(first(vent, "state", "status", "active", default="Unknown"))

        captured = safe_str(first(data, "timestamp", "capturedAt", "lastUpdated", default=""))

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
            captured_at=captured, raw=data,
        )

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            return cls()
        allowed = {k: v for k, v in data.items() if k in cls.__dataclass_fields__ and k != "raw"}
        return cls(**allowed)
