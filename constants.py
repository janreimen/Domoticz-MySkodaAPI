PLUGIN_VERSION = "0.0.2-alpha"
PLUGIN_KEY = "MySkodaAPI"
PLUGIN_NAME = "MySkoda API Integration"
API_BASE = "https://public.api.connect.skoda-auto.cz"
VEHICLE_ENDPOINT = "/api/v1/vehicles/{vin}"
API_TIMEOUT = 30
DEFAULT_POLL_MINUTES = 30
MIN_POLL_MINUTES = 15
MAX_POLL_MINUTES = 60
USER_AGENT = "Domoticz-MySkodaAPI/{}".format(PLUGIN_VERSION)
API_INCLUDE = [
    "info", "status", "fuelStatus", "odometer", "parkingPosition",
    "airConditioning", "auxiliaryHeating", "activeVentilation",
]

# Stable Domoticz unit IDs. Do not renumber existing units.
UNITS = {
    "vehicle": 1, "doors_locked": 2, "doors": 3, "windows": 4,
    "lights": 5, "trunk": 6, "bonnet": 7, "sunroof": 8,
    "fuel_level": 9, "fuel_range": 10, "total_range": 11,
    "odometer": 12, "vehicle_state": 13, "parking_address": 14,
    "parking_gps": 15, "air_conditioning": 16, "target_temperature": 17,
    "auxiliary_heating": 18, "active_ventilation": 19,
    "vehicle_captured": 20, "api_key_expiry": 21,
    "api_rate_limit": 22, "api_status": 23,
}

SELECTORS = {
    "doors_locked": ["UNKNOWN", "YES", "NO", "OPENED", "TRUNK_OPENED"],
    "doors": ["UNKNOWN", "OPEN", "CLOSED"],
    "windows": ["UNKNOWN", "OPEN", "CLOSED", "UNSUPPORTED"],
    "lights": ["UNKNOWN", "ON", "OFF"],
    "trunk": ["UNKNOWN", "OPEN", "CLOSED", "UNSUPPORTED"],
    "bonnet": ["UNKNOWN", "OPEN", "CLOSED", "UNSUPPORTED"],
    "sunroof": ["UNKNOWN", "OPEN", "CLOSED", "UNSUPPORTED"],
    "vehicle_state": ["UNKNOWN", "PARKED", "IN_MOTION"],
    "air_conditioning": ["UNKNOWN", "OFF", "COOLING", "HEATING", "HEATING_AUXILIARY", "VENTILATION", "COMPLETED", "UNSUPPORTED"],
    "auxiliary_heating": ["UNKNOWN", "OFF", "PREHEATING", "HEATING_AUXILIARY", "VENTILATION", "UNSUPPORTED"],
    "active_ventilation": ["UNKNOWN", "OFF", "PREHEATING", "VENTILATION", "UNSUPPORTED"],
}
