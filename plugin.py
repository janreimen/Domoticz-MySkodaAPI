#!/usr/bin/env python3

"""
<plugin
    key="MySkodaAPI"
    name="MySkoda API Integration"
    author="Jan Reimen"
    version="0.0.1-beta"
    externallink="https://github.com/janreimen/Domoticz-MySkodaAPI">

    <description>
        MyŠkoda Public API integration for Domoticz.

        Read-only integration for Škoda vehicles using the official
        MyŠkoda Public API.

        This beta version does not implement remote vehicle commands.
    </description>

    <params>
        <param field="Username" label="Vehicle VIN" width="350px">
            <description>
                Vehicle VIN, for example TMBJV0NX0TY076609
            </description>
        </param>

        <param field="Password" label="MyŠkoda API Key" password="true" width="350px">
            <description>
                API key created in the MyŠkoda application
            </description>
        </param>

        <param field="Mode1" label="Poll interval" width="100px">
            <options>
                <option label="15 minutes" value="15"/>
                <option label="30 minutes" value="30" default="true"/>
                <option label="60 minutes" value="60"/>
            </options>
        </param>

        <param field="Mode2" label="Debug" width="100px">
            <options>
                <option label="Normal" value="0" default="true"/>
                <option label="Debug" value="1"/>
            </options>
        </param>
    </params>
</plugin>
"""

import Domoticz
import json
import time
import urllib.error
import urllib.parse
import urllib.request


# ============================================================================
# Configuration
# ============================================================================

PLUGIN_VERSION = "0.0.1-beta"

API_BASE = "https://public.api.connect.skoda-auto.cz"
VEHICLE_ENDPOINT = "/api/v1/vehicles/{vin}"

API_TIMEOUT = 30

DEFAULT_POLL_MINUTES = 30

USER_AGENT = "Domoticz-MySkodaAPI/{}".format(PLUGIN_VERSION)


# Explicitly request the sections supported by this read-only beta plugin.
API_INCLUDE = [
    "info",
    "status",
    "fuelStatus",
    "odometer",
    "parkingPosition",
    "airConditioning",
    "auxiliaryHeating",
    "activeVentilation",
]


# ============================================================================
# Helpers
# ============================================================================


def safe_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def iso_to_text(value):
    """
    Convert an ISO timestamp into a compact human-readable string.

    The API normally returns UTC timestamps ending in Z.
    """
    if not value:
        return None

    try:
        text = str(value)
        if text.endswith("Z"):
            text = text[:-1] + " UTC"
        return text
    except Exception:
        return None


# ============================================================================
# Plugin
# ============================================================================


class BasePlugin:
    def __init__(self):

        self.vin = ""
        self.api_key = ""

        self.poll_minutes = DEFAULT_POLL_MINUTES
        self.debug = False

        self.last_poll = 0

        self.api_key_expires = ""
        self.rate_limit = ""
        self.api_status = ""

        self.initialized = False

    # ========================================================================
    # Logging
    # ========================================================================

    def log(self, message):

        Domoticz.Log("[MySkoda] {}".format(message))

    def debug_log(self, message):

        if self.debug:
            Domoticz.Debug("[MySkoda] {}".format(message))

    def error(self, message):

        Domoticz.Error("[MySkoda] {}".format(message))

    # ========================================================================
    # Selector helpers
    # ========================================================================

    @staticmethod
    def selector_options(level_names):

        return {
            "LevelNames": "|".join(level_names),
            "LevelActions": "|" * (len(level_names) - 1),
            "LevelOffHidden": "false",
            "SelectorStyle": "0",
        }

    def create_selector(self, unit, name, level_names):

        options = self.selector_options(level_names)

        Domoticz.Device(
            Name=name, Unit=unit, TypeName="Selector Switch", Options=options, Used=1
        ).Create()

    def update_selector(self, unit, value, level_names):

        if unit not in Devices:
            return

        if value is None:
            return

        value = str(value)

        try:
            level = level_names.index(value)
        except ValueError:
            self.debug_log(
                "Unknown selector value '{}' for unit {}".format(value, unit)
            )
            return

        # Selector levels are 0, 10, 20, 30, ...
        nvalue = level * 10

        Devices[unit].Update(nValue=nvalue, sValue=str(nvalue))

    # ========================================================================
    # Text devices
    # ========================================================================

    def create_text(self, unit, name):

        Domoticz.Device(Name=name, Unit=unit, TypeName="Text", Used=1).Create()

    def update_text(self, unit, value):

        if unit not in Devices:
            return

        if value is None:
            return

        Devices[unit].Update(nValue=0, sValue=str(value))

    # ========================================================================
    # Percentage
    # ========================================================================

    def create_percentage(self, unit, name):

        Domoticz.Device(Name=name, Unit=unit, TypeName="Percentage", Used=1).Create()

    def update_percentage(self, unit, value):

        if unit not in Devices:
            return

        if value is None:
            return

        value = safe_int(value)

        if value is None:
            return

        value = max(0, min(100, value))

        Devices[unit].Update(nValue=value, sValue=str(value))

    # ========================================================================
    # Distance
    # ========================================================================

    def create_distance(self, unit, name):

        Domoticz.Device(
            Name=name,
            Unit=unit,
            Type=243,
            Subtype=31,
            Switchtype=0,
            Options={"Custom": "1;km"},
            Used=1,
        ).Create()

    def update_distance(self, unit, value):

        if unit not in Devices:
            return

        if value is None:
            return

        value = safe_float(value)

        if value is None:
            return

        # Keep the API's native unit: kilometres.
        Devices[unit].Update(nValue=0, sValue="{:.1f}".format(value))

    # ========================================================================
    # Temperature
    # ========================================================================

    def create_temperature(self, unit, name):

        Domoticz.Device(Name=name, Unit=unit, TypeName="Temperature", Used=1).Create()

    def update_temperature(self, unit, value):

        if unit not in Devices:
            return

        if value is None:
            return

        value = safe_float(value)

        if value is None:
            return

        Devices[unit].Update(nValue=0, sValue="{:.1f}".format(value))

    # ========================================================================
    # Device creation
    # ========================================================================

    def create_devices(self):

        self.log("Creating Domoticz devices")

        # --------------------------------------------------------------------
        # Vehicle information
        # --------------------------------------------------------------------

        self.create_text(1, "Vehicle")

        # --------------------------------------------------------------------
        # Vehicle status selectors
        # --------------------------------------------------------------------

        self.create_selector(
            2,
            "Doors Locked",
            [
                "UNKNOWN",
                "YES",
                "NO",
                "OPENED",
                "TRUNK_OPENED",
            ],
        )

        self.create_selector(
            3,
            "Doors",
            [
                "UNKNOWN",
                "OPEN",
                "CLOSED",
            ],
        )

        self.create_selector(
            4,
            "Windows",
            [
                "UNKNOWN",
                "OPEN",
                "CLOSED",
                "UNSUPPORTED",
            ],
        )

        self.create_selector(
            5,
            "Lights",
            [
                "UNKNOWN",
                "ON",
                "OFF",
            ],
        )

        self.create_selector(
            6,
            "Trunk",
            [
                "UNKNOWN",
                "OPEN",
                "CLOSED",
                "UNSUPPORTED",
            ],
        )

        self.create_selector(
            7,
            "Bonnet",
            [
                "UNKNOWN",
                "OPEN",
                "CLOSED",
                "UNSUPPORTED",
            ],
        )

        self.create_selector(
            8,
            "Sunroof",
            [
                "UNKNOWN",
                "OPEN",
                "CLOSED",
                "UNSUPPORTED",
            ],
        )

        # --------------------------------------------------------------------
        # Fuel
        # --------------------------------------------------------------------

        self.create_percentage(9, "Fuel Level")

        self.create_distance(10, "Fuel Range")

        self.create_distance(11, "Total Range")

        # --------------------------------------------------------------------
        # Vehicle movement / parking
        # --------------------------------------------------------------------

        self.create_distance(12, "Odometer")

        self.create_selector(
            13,
            "Vehicle State",
            [
                "UNKNOWN",
                "PARKED",
                "IN_MOTION",
            ],
        )

        self.create_text(14, "Parking Address")

        self.create_text(15, "Parking GPS")

        # --------------------------------------------------------------------
        # Air conditioning
        # --------------------------------------------------------------------

        self.create_selector(
            16,
            "Air Conditioning",
            [
                "UNKNOWN",
                "OFF",
                "COOLING",
                "HEATING",
                "HEATING_AUXILIARY",
                "VENTILATION",
                "COMPLETED",
                "UNSUPPORTED",
            ],
        )

        self.create_temperature(17, "Target Temperature")

        # --------------------------------------------------------------------
        # Auxiliary heating
        # --------------------------------------------------------------------

        self.create_selector(
            18,
            "Auxiliary Heating",
            [
                "UNKNOWN",
                "OFF",
                "PREHEATING",
                "HEATING_AUXILIARY",
                "VENTILATION",
                "UNSUPPORTED",
            ],
        )

        # --------------------------------------------------------------------
        # Active ventilation
        # --------------------------------------------------------------------

        self.create_selector(
            19,
            "Active Ventilation",
            [
                "UNKNOWN",
                "OFF",
                "PREHEATING",
                "VENTILATION",
                "UNSUPPORTED",
            ],
        )

        # --------------------------------------------------------------------
        # API information
        # --------------------------------------------------------------------

        self.create_text(20, "Vehicle Captured")

        self.create_text(21, "API Key Expiry")

        self.create_text(22, "API Rate Limit")

        self.create_text(23, "API Status")

    # ========================================================================
    # API
    # ========================================================================

    def build_url(self):

        encoded_vin = urllib.parse.quote(self.vin, safe="")

        endpoint = VEHICLE_ENDPOINT.format(vin=encoded_vin)

        query = urllib.parse.urlencode([("include", ",".join(API_INCLUDE))])

        return API_BASE + endpoint + "?" + query

    def api_request(self):

        url = self.build_url()

        headers = {
            "X-API-Key": self.api_key,
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }

        request = urllib.request.Request(url, headers=headers, method="GET")

        self.debug_log("Requesting vehicle data")

        try:

            with urllib.request.urlopen(request, timeout=API_TIMEOUT) as response:

                status_code = response.getcode()

                body = response.read().decode("utf-8", errors="replace")

                # ------------------------------------------------------------
                # API headers
                # ------------------------------------------------------------

                expires = response.headers.get("X-API-Key-Expires-At")

                if expires:
                    self.api_key_expires = expires

                rate_remaining = response.headers.get("RateLimit-Remaining")

                rate_limit = response.headers.get("RateLimit-Limit")

                rate_reset = response.headers.get("RateLimit-Reset")

                if (
                    rate_remaining is not None
                    or rate_limit is not None
                    or rate_reset is not None
                ):

                    self.rate_limit = "Remaining={}; Limit={}; Reset={}".format(
                        rate_remaining or "?", rate_limit or "?", rate_reset or "?"
                    )

                self.api_status = "HTTP {}".format(status_code)

                if status_code != 200:

                    self.error("Unexpected HTTP status {}".format(status_code))

                    return None

                try:

                    data = json.loads(body)

                except json.JSONDecodeError as exc:

                    self.error("Invalid JSON response: {}".format(exc))

                    return None

                return data

        except urllib.error.HTTPError as exc:

            status_code = exc.code

            self.api_status = "HTTP {}".format(status_code)

            # ------------------------------------------------------------
            # Capture useful rate-limit information even on errors.
            # ------------------------------------------------------------

            retry_after = exc.headers.get("Retry-After")

            rate_remaining = exc.headers.get("RateLimit-Remaining")

            rate_limit = exc.headers.get("RateLimit-Limit")

            rate_reset = exc.headers.get("RateLimit-Reset")

            if (
                rate_remaining is not None
                or rate_limit is not None
                or rate_reset is not None
            ):

                self.rate_limit = "Remaining={}; Limit={}; Reset={}".format(
                    rate_remaining or "?", rate_limit or "?", rate_reset or "?"
                )

            # ------------------------------------------------------------
            # Error messages
            # ------------------------------------------------------------

            if status_code == 400:

                self.error("HTTP 400 Bad Request")

            elif status_code == 401:

                self.error("HTTP 401 Unauthorized - check the API key")

            elif status_code == 403:

                self.error(
                    "HTTP 403 Forbidden - API key may not be "
                    "authorized for this vehicle"
                )

            elif status_code == 404:

                self.error("HTTP 404 Not Found - vehicle not found")

            elif status_code == 422:

                self.error("HTTP 422 Unprocessable Entity")

            elif status_code == 429:

                if retry_after:

                    self.error(
                        "HTTP 429 Too Many Requests - Retry-After: {}".format(
                            retry_after
                        )
                    )

                else:

                    self.error("HTTP 429 Too Many Requests")

            elif status_code == 500:

                self.error("HTTP 500 Internal Server Error")

            elif status_code == 503:

                self.error("HTTP 503 Service Unavailable")

            elif status_code == 504:

                self.error("HTTP 504 Gateway Timeout")

            else:

                self.error("HTTP {} returned by MyŠkoda API".format(status_code))

            return None

        except urllib.error.URLError as exc:

            self.api_status = "Connection error"

            self.error("Connection error: {}".format(exc.reason))

            return None

        except TimeoutError:

            self.api_status = "Timeout"

            self.error("API request timed out after {} seconds".format(API_TIMEOUT))

            return None

        except Exception as exc:

            self.api_status = "Error"

            self.error("Unexpected API error: {}".format(exc))

            return None

    # ========================================================================
    # API data processing
    # ========================================================================

    def update_from_api(self, data):

        if not data:
            return

        vehicle = data.get("vehicle")

        if not isinstance(vehicle, dict):

            self.error("API response does not contain a valid vehicle object")

            return

        self.debug_log("Processing vehicle response")

        # --------------------------------------------------------------------
        # Vehicle information
        # --------------------------------------------------------------------

        name = vehicle.get("name")

        if name is not None:

            self.update_text(1, name)

        # --------------------------------------------------------------------
        # Status
        # --------------------------------------------------------------------

        status = vehicle.get("status")

        if isinstance(status, dict):

            overall = status.get("overall")

            if isinstance(overall, dict):

                self.update_selector(
                    2,
                    overall.get("doorsLocked"),
                    [
                        "UNKNOWN",
                        "YES",
                        "NO",
                        "OPENED",
                        "TRUNK_OPENED",
                    ],
                )

                self.update_selector(
                    3,
                    overall.get("doors"),
                    [
                        "UNKNOWN",
                        "OPEN",
                        "CLOSED",
                    ],
                )

                self.update_selector(
                    4,
                    overall.get("windows"),
                    [
                        "UNKNOWN",
                        "OPEN",
                        "CLOSED",
                        "UNSUPPORTED",
                    ],
                )

                self.update_selector(
                    5,
                    overall.get("lights"),
                    [
                        "UNKNOWN",
                        "ON",
                        "OFF",
                    ],
                )

            detail = status.get("detail")

            if isinstance(detail, dict):

                self.update_selector(
                    6,
                    detail.get("trunk"),
                    [
                        "UNKNOWN",
                        "OPEN",
                        "CLOSED",
                        "UNSUPPORTED",
                    ],
                )

                self.update_selector(
                    7,
                    detail.get("bonnet"),
                    [
                        "UNKNOWN",
                        "OPEN",
                        "CLOSED",
                        "UNSUPPORTED",
                    ],
                )

                self.update_selector(
                    8,
                    detail.get("sunroof"),
                    [
                        "UNKNOWN",
                        "OPEN",
                        "CLOSED",
                        "UNSUPPORTED",
                    ],
                )

            captured = status.get("carCapturedTimestamp")

            if captured:

                self.update_text(20, iso_to_text(captured))

        # --------------------------------------------------------------------
        # Fuel status
        # --------------------------------------------------------------------

        fuel = vehicle.get("fuelStatus")

        if isinstance(fuel, dict):

            primary = fuel.get("primaryEngineRange")

            if isinstance(primary, dict):

                fuel_level = primary.get("currentFuelLevelInPercent")

                if fuel_level is not None:

                    self.update_percentage(9, fuel_level)

                fuel_range = primary.get("remainingRangeInKm")

                if fuel_range is not None:

                    self.update_distance(10, fuel_range)

            total_range = fuel.get("totalRangeInKm")

            if total_range is not None:

                self.update_distance(11, total_range)

        # --------------------------------------------------------------------
        # Odometer
        # --------------------------------------------------------------------

        odometer = vehicle.get("odometer")

        if isinstance(odometer, dict):

            mileage = odometer.get("mileageInKm")

            if mileage is not None:

                self.update_distance(12, mileage)

        # --------------------------------------------------------------------
        # Parking position
        # --------------------------------------------------------------------

        parking = vehicle.get("parkingPosition")

        if isinstance(parking, dict):

            parking_state = parking.get("state")

            if parking_state is not None:

                self.update_selector(
                    13,
                    parking_state,
                    [
                        "UNKNOWN",
                        "PARKED",
                        "IN_MOTION",
                    ],
                )

            address = parking.get("formattedAddress")

            if address is not None:

                self.update_text(14, address)

            coordinates = parking.get("gpsCoordinates")

            if isinstance(coordinates, dict):

                latitude = coordinates.get("latitude")

                longitude = coordinates.get("longitude")

                if latitude is not None and longitude is not None:

                    gps = "{:.6f}, {:.6f}".format(float(latitude), float(longitude))

                    self.update_text(15, gps)

        # --------------------------------------------------------------------
        # Air conditioning
        # --------------------------------------------------------------------

        air_conditioning = vehicle.get("airConditioning")

        # IMPORTANT:
        # If this section is absent from the API response, nothing is changed.
        if isinstance(air_conditioning, dict):

            self.update_selector(
                16,
                air_conditioning.get("state"),
                [
                    "UNKNOWN",
                    "OFF",
                    "COOLING",
                    "HEATING",
                    "HEATING_AUXILIARY",
                    "VENTILATION",
                    "COMPLETED",
                    "UNSUPPORTED",
                ],
            )

            target_temperature = air_conditioning.get("targetTemperature")

            if isinstance(target_temperature, dict):

                temperature = target_temperature.get("value")

                if temperature is not None:

                    self.update_temperature(17, temperature)

        # --------------------------------------------------------------------
        # Auxiliary heating
        # --------------------------------------------------------------------

        auxiliary_heating = vehicle.get("auxiliaryHeating")

        # IMPORTANT:
        # Missing section means "no update", not UNKNOWN.
        if isinstance(auxiliary_heating, dict):

            self.update_selector(
                18,
                auxiliary_heating.get("state"),
                [
                    "UNKNOWN",
                    "OFF",
                    "PREHEATING",
                    "HEATING_AUXILIARY",
                    "VENTILATION",
                    "UNSUPPORTED",
                ],
            )

        # --------------------------------------------------------------------
        # Active ventilation
        # --------------------------------------------------------------------

        active_ventilation = vehicle.get("activeVentilation")

        # IMPORTANT:
        # Missing section means "no update", not UNKNOWN.
        if isinstance(active_ventilation, dict):

            self.update_selector(
                19,
                active_ventilation.get("state"),
                [
                    "UNKNOWN",
                    "OFF",
                    "PREHEATING",
                    "VENTILATION",
                    "UNSUPPORTED",
                ],
            )

        # --------------------------------------------------------------------
        # API information
        # --------------------------------------------------------------------

        if self.api_key_expires:

            self.update_text(21, iso_to_text(self.api_key_expires))

        if self.rate_limit:

            self.update_text(22, self.rate_limit)

        if self.api_status:

            self.update_text(23, self.api_status)

    # ========================================================================
    # Poll
    # ========================================================================

    def poll(self):

        self.debug_log("Starting API poll")

        data = self.api_request()

        if data is None:

            if self.api_status:

                self.update_text(23, self.api_status)

            if self.rate_limit:

                self.update_text(22, self.rate_limit)

            return

        self.update_from_api(data)

        self.debug_log("API poll completed successfully")

    # ========================================================================
    # Domoticz callbacks
    # ========================================================================

    def onStart(self):

        self.log("Starting MyŠkoda API Integration {}".format(PLUGIN_VERSION))

        # --------------------------------------------------------------------
        # Configuration
        # --------------------------------------------------------------------

        self.vin = Parameters.get("Username", "").strip()

        self.api_key = Parameters.get("Password", "").strip()

        poll_value = Parameters.get("Mode1", str(DEFAULT_POLL_MINUTES))

        self.poll_minutes = safe_int(poll_value, DEFAULT_POLL_MINUTES)

        if self.poll_minutes not in (
            15,
            30,
            60,
        ):

            self.poll_minutes = DEFAULT_POLL_MINUTES

        self.debug = Parameters.get("Mode2", "0") == "1"

        # --------------------------------------------------------------------
        # Validate configuration
        # --------------------------------------------------------------------

        if not self.vin:

            self.error("Vehicle VIN is not configured")

        if not self.api_key:

            self.error("MyŠkoda API key is not configured")

        # --------------------------------------------------------------------
        # Create devices if required
        # --------------------------------------------------------------------

        if len(Devices) == 0:

            self.create_devices()

        else:

            self.debug_log("{} existing MySkoda devices found".format(len(Devices)))

        self.initialized = True

        # --------------------------------------------------------------------
        # Immediate first poll
        # --------------------------------------------------------------------

        if self.vin and self.api_key:

            self.poll()

            self.last_poll = time.time()

    def onStop(self):

        self.log("Stopping MyŠkoda API Integration")

    def onHeartbeat(self):

        if not self.initialized:

            return

        if not self.vin or not self.api_key:

            return

        now = time.time()

        interval = self.poll_minutes * 60

        if self.last_poll == 0 or now - self.last_poll >= interval:

            self.poll()

            self.last_poll = now

    def onCommand(self, Unit, Command, Level, Color):

        # --------------------------------------------------------------------
        # This beta plugin is intentionally read-only.
        #
        # Selector devices are used to represent API state, but clicking
        # them does NOT send commands to the vehicle.
        #
        # The next API poll restores the actual vehicle state.
        # --------------------------------------------------------------------

        self.debug_log(
            "Ignoring command for Unit {} " "(read-only beta plugin)".format(Unit)
        )


# ============================================================================
# Plugin instance
# ============================================================================

global _plugin
_plugin = BasePlugin()


def onStart():
    _plugin.onStart()


def onStop():
    _plugin.onStop()


def onHeartbeat():
    _plugin.onHeartbeat()


def onCommand(Unit, Command, Level, Color):
    _plugin.onCommand(Unit, Command, Level, Color)

