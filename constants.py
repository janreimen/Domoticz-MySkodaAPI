PLUGIN_VERSION = "0.4.4.002"
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
    # New in 0.4.3-alpha. Appended after 44 so existing units 1-44 are untouched
    # on upgrade (same convention as the 0.4.2 comment above).
    "charging_power": 45,
    "remaining_charging_time": 46,
    "charge_type": 47,
    # New in 0.4.3.1-003-alpha (v1.1.0 API release: plugLockState). Appended
    # after 47 for the same upgrade-safety reason as above.
    "plug_lock_state": 48,
    # New in 0.4.4.0: first writable (command) device, appended after 48 for
    # the same upgrade-safety reason as above. See WRITABLE_UNITS below.
    "air_conditioning_control": 49,
    # New in 0.4.4.002: two more writable (command) devices, appended after
    # 49 for the same upgrade-safety reason as above.
    "active_ventilation_control": 50,
    "auxiliary_heating_control": 51,
}

# Units that onCommand() treats as real vehicle commands instead of
# read-only telemetry. Everything else is ignored and immediately restored
# to the last API-derived state (see plugin.py's onCommand and
# devices.py's restore_selector). Centralized here so onCommand's dispatch
# logic doesn't need updating every time a new command unit is added.
WRITABLE_UNITS = {
    UNITS["air_conditioning_control"],
    UNITS["active_ventilation_control"],
    UNITS["auxiliary_heating_control"],
}

RETRYABLE_STATUS = {429, 500, 502, 503, 504}
MAX_RETRIES = 3
INITIAL_BACKOFF = 2.0
MAX_BACKOFF = 60.0

STATE_CACHE_FILENAME = "myskoda_last_state.json"
DISTANCE_STATE_FILENAME = "myskoda_distance_state.json"

# --- Remote vehicle commands (new in 0.4.4.0) -------------------------------
#
# CONFIRMED against the real OpenAPI spec (myskoda-public-api.yaml, v1.1.0):
#   - POST {vehicle}/air-conditioning/start - requestBody required: true,
#     schema StartAirConditioningConfiguration {targetTemperature,
#     airConditioningWithoutExternalPower}. No security PIN ("spin") field
#     on this endpoint - spin is only required by
#     StartAuxiliaryHeatingConfiguration (POST .../auxiliary-heating/start),
#     a separate, not-yet-implemented command.
#   - POST {vehicle}/air-conditioning/stop - no request body.
#   - Both return 202 Accepted with the same RateLimit-*/X-API-Key-Expires-At
#     headers as the main vehicle GET.
#   - targetTemperature is the TargetTemperature schema: {value, unit}, e.g.
#     {"value": 21.0, "unit": "CELSIUS"} - matches the read-side shape
#     already relied on elsewhere in this plugin.
# See ENABLE_VEHICLE_COMMANDS (Mode4) in plugin.py, which still gates all
# command-sending off by default.
AIR_CONDITIONING_START_ENDPOINT = VEHICLE_ENDPOINT + "/air-conditioning/start"
AIR_CONDITIONING_STOP_ENDPOINT = VEHICLE_ENDPOINT + "/air-conditioning/stop"
DEFAULT_AC_TARGET_TEMPERATURE_CELSIUS = 21.0

# --- Active Ventilation and Auxiliary Heating commands (new in 0.4.4.002) --
#
# CONFIRMED against the real OpenAPI spec:
#   - POST {vehicle}/active-ventilation/start and .../stop - neither takes a
#     request body at all, and neither needs a security PIN.
#   - POST {vehicle}/auxiliary-heating/start - requestBody required: true,
#     schema StartAuxiliaryHeatingConfiguration {targetTemperature, spin,
#     durationInSeconds, startMode}. "spin" (the vehicle's Security PIN) is
#     the only required field - this plugin sends just {"spin": <pin>} and
#     leaves temperature/duration/startMode at the vehicle's own defaults.
#   - POST {vehicle}/auxiliary-heating/stop - no request body, no PIN
#     needed to stop.
# All four return 202 Accepted with the same RateLimit-*/X-API-Key-Expires-At
# headers as the main vehicle GET. See ENABLE_VEHICLE_COMMANDS (Mode4) in
# plugin.py, which still gates all command-sending off by default, and
# Mode5 (Auxiliary Heating PIN) which gates auxiliary heating specifically.
ACTIVE_VENTILATION_START_ENDPOINT = VEHICLE_ENDPOINT + "/active-ventilation/start"
ACTIVE_VENTILATION_STOP_ENDPOINT = VEHICLE_ENDPOINT + "/active-ventilation/stop"
AUXILIARY_HEATING_START_ENDPOINT = VEHICLE_ENDPOINT + "/auxiliary-heating/start"
AUXILIARY_HEATING_STOP_ENDPOINT = VEHICLE_ENDPOINT + "/auxiliary-heating/stop"
