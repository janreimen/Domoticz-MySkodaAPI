from dataclasses import dataclass
from typing import Optional, Any, Dict

from utils import safe_float


@dataclass
class VehicleState:
    name: Optional[str] = None
    doors_locked: Optional[str] = None
    doors: Optional[str] = None
    windows: Optional[str] = None
    lights: Optional[str] = None
    trunk: Optional[str] = None
    bonnet: Optional[str] = None
    sunroof: Optional[str] = None
    fuel_level: Optional[int] = None
    fuel_range_km: Optional[float] = None
    total_range_km: Optional[float] = None
    odometer_km: Optional[float] = None
    vehicle_state: Optional[str] = None
    parking_address: Optional[str] = None
    parking_gps: Optional[str] = None
    air_conditioning: Optional[str] = None
    target_temperature: Optional[float] = None
    auxiliary_heating: Optional[str] = None
    active_ventilation: Optional[str] = None
    vehicle_captured: Optional[str] = None


def parse_vehicle(data: Dict[str, Any], logger=None) -> Optional[VehicleState]:
    if not isinstance(data, dict):
        return None
    vehicle = data.get("vehicle")
    if not isinstance(vehicle, dict):
        return None

    state = VehicleState(name=vehicle.get("name"))
    status = vehicle.get("status")
    if isinstance(status, dict):
        overall = status.get("overall")
        if isinstance(overall, dict):
            state.doors_locked = overall.get("doorsLocked")
            state.doors = overall.get("doors")
            state.windows = overall.get("windows")
            state.lights = overall.get("lights")
        detail = status.get("detail")
        if isinstance(detail, dict):
            state.trunk = detail.get("trunk")
            state.bonnet = detail.get("bonnet")
            state.sunroof = detail.get("sunroof")
        state.vehicle_captured = status.get("carCapturedTimestamp")

    fuel = vehicle.get("fuelStatus")
    if isinstance(fuel, dict):
        primary = fuel.get("primaryEngineRange")
        if isinstance(primary, dict):
            state.fuel_level = _bounded_percent(primary.get("currentFuelLevelInPercent"))
            state.fuel_range_km = safe_float(primary.get("remainingRangeInKm"))
        state.total_range_km = safe_float(fuel.get("totalRangeInKm"))

    odometer = vehicle.get("odometer")
    if isinstance(odometer, dict):
        state.odometer_km = safe_float(odometer.get("mileageInKm"))

    parking = vehicle.get("parkingPosition")
    if isinstance(parking, dict):
        state.vehicle_state = parking.get("state")
        state.parking_address = parking.get("formattedAddress")
        coordinates = parking.get("gpsCoordinates")
        if isinstance(coordinates, dict):
            lat = safe_float(coordinates.get("latitude"))
            lon = safe_float(coordinates.get("longitude"))
            if lat is not None and lon is not None:
                state.parking_gps = "{:.6f}, {:.6f}".format(lat, lon)

    ac = vehicle.get("airConditioning")
    if isinstance(ac, dict):
        state.air_conditioning = ac.get("state")
        target = ac.get("targetTemperature")
        if isinstance(target, dict):
            state.target_temperature = safe_float(target.get("value"))

    aux = vehicle.get("auxiliaryHeating")
    if isinstance(aux, dict):
        state.auxiliary_heating = aux.get("state")

    ventilation = vehicle.get("activeVentilation")
    if isinstance(ventilation, dict):
        state.active_ventilation = ventilation.get("state")

    return state


def _bounded_percent(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return None
    return max(0, min(100, value))
