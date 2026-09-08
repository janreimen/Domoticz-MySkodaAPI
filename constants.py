PLUGIN_VERSION = "0.4.1"
PLUGIN_KEY = "MySkodaAPI"
PLUGIN_NAME = "MySkoda API Integration"
PLUGIN_URL = "https://github.com/janreimen/Domoticz-MySkodaAPI"

API_BASE = "https://public.api.connect.skoda-auto.cz"
VEHICLE_ENDPOINT = "/api/v1/vehicles/{vin}"
API_TIMEOUT = 30
DEFAULT_POLL_MINUTES = 30
MIN_POLL_MINUTES = 15
MAX_POLL_MINUTES = 60
API_KEY_EXPIRY_WARNING_DAYS = 30
USER_AGENT = "Domoticz-MySkodaAPI/{}".format(PLUGIN_VERSION)

API_INCLUDE = [
    "info", "status", "fuelStatus", "odometer", "parkingPosition",
    "airConditioning", "auxiliaryHeating", "activeVentilation", "charging",
]

# Existing unit IDs are intentionally preserved for upgrade compatibility.
UNITS = {
    "vehicle": 1,
    "doors_locked": 2,
    "doors": 3,
    "windows": 4,
    "lights": 5,
    "trunk": 6,
    "bonnet": 7,
    "sunroof": 8,
    "fuel_level": 9,
    "fuel_range": 10,
    "total_range": 11,
    "odometer": 12,
    "vehicle_state": 13,
    "parking_address": 14,
    "parking_gps": 15,
    "air_conditioning": 16,
    "target_temperature": 17,
    "auxiliary_heating": 18,
    "active_ventilation": 19,
    "vehicle_captured": 20,
    "api_key_expiry": 21,
    "api_rate_limit": 22,
    "api_status": 23,
    "today_distance": 24,
    "yesterday_distance": 25,
    "vehicle_security": 26,
    "climate_state": 27,
    "data_quality": 28,
    "fuel_type": 29,
    "charging_state": 30,
    "battery_soc": 31,
    "electric_range": 32,
    "charging_connected": 33,
    "charge_target": 34,
    "charge_mode": 35,
    "charging_captured": 36,
    "fuel_captured": 37,
    "odometer_captured": 38,
    "api_capabilities": 39,
    "api_errors": 40,
    "supported_operations": 41,
    "api_rate_remaining": 42,
    "api_rate_reset": 43,
    "api_key_status": 44,
}

RETRYABLE_STATUS = {429, 500, 502, 503, 504}
MAX_RETRIES = 3
INITIAL_BACKOFF = 2.0
MAX_BACKOFF = 60.0

STATE_CACHE_FILENAME = "myskoda_last_state.json"
DISTANCE_STATE_FILENAME = "myskoda_distance_state.json"
