import unittest

from myskoda_api import APIResult
from vehicle import VehicleState
from devices import DeviceManager


class VehicleParserTests(unittest.TestCase):
    def sample(self):
        return {"vehicle": {
            "fuelStatus": {"primaryEngineRange": {"currentFuelLevelInPercent": 100, "remainingRangeInKm": 640}, "totalRangeInKm": 640},
            "licensePlate": "TEST", "name": "Octavia RS",
            "odometer": {"mileageInKm": 7232, "carCapturedTimestamp": "2026-09-05T07:04:51Z"},
            "parkingPosition": {"state": "PARKED", "formattedAddress": "Luxembourg", "gpsCoordinates": {"latitude": 49.6, "longitude": 6.1}},
            "auxiliaryHeating": {"state": "OFF", "targetTemperature": {"value": 21.0, "unit": "CELSIUS"}},
            "status": {"overall": {"doorsLocked": "YES", "doors": "CLOSED", "windows": "OPEN", "lights": "OFF"}, "detail": {"sunroof": "CLOSED", "trunk": "CLOSED", "bonnet": "CLOSED"}, "carCapturedTimestamp": "2026-09-05T07:04:51Z"},
            "vin": "TESTVIN"
        }}

    def test_current_api_vehicle_wrapper(self):
        state = VehicleState.from_api(self.sample())
        self.assertEqual(state.vin, "TESTVIN")
        self.assertTrue(state.doors_locked)
        self.assertEqual(state.windows, "OPEN")
        self.assertEqual(state.fuel_level, 100.0)
        self.assertEqual(state.fuel_range, 640.0)
        self.assertEqual(state.total_range, 640.0)
        self.assertEqual(state.odometer, 7232.0)
        self.assertEqual(state.parking_state, "PARKED")
        self.assertEqual(state.target_temperature, 21.0)

    def test_legacy_flat_vehicle_is_still_supported(self):
        data = {"info": {"vin": "WVWTEST", "name": "Octavia RS", "licensePlate": "L-TEST"}, "status": {"doorsLocked": True, "doors": "closed", "windows": "closed", "lights": "off"}, "fuelStatus": {"fuelLevel": 55, "fuelRange": 420, "totalRange": 600}, "odometer": {"value": 12345}}
        state = VehicleState.from_api(data)
        self.assertEqual(state.name, "Octavia RS")
        self.assertTrue(state.doors_locked)
        self.assertEqual(state.odometer, 12345.0)

    def test_missing_fields_are_safe(self):
        state = VehicleState.from_api({"vehicle": {"name": "Car"}})
        self.assertEqual(state.name, "Car")
        self.assertIsNone(state.fuel_level)
        self.assertEqual(state.doors, "Unknown")

    def test_rate_limit_and_expiry_headers(self):
        result = APIResult(headers={"ratelimit-limit": "20", "ratelimit-remaining": "15", "ratelimit-reset": "873", "x-api-key-expires-at": "2027-03-04T13:44:43.043Z"})
        self.assertIn("limit=20", result.rate_text)
        self.assertEqual(result.api_key_expires_at, "2027-03-04T13:44:43.043Z")


class SmartStateTests(unittest.TestCase):
    def state(self, locked=True, doors="CLOSED", windows="CLOSED", trunk="CLOSED", bonnet="CLOSED", sunroof="CLOSED", ac="OFF", heat="OFF", vent="OFF", parking="PARKED"):
        return VehicleState(doors_locked=locked, doors=doors, windows=windows, trunk=trunk, bonnet=bonnet, sunroof=sunroof, air_conditioning=ac, auxiliary_heating=heat, active_ventilation=vent, parking_state=parking, vehicle_state=parking)

    def test_secure_vehicle(self):
        self.assertEqual(DeviceManager._smart_security(self.state()), "SECURE")

    def test_attention_when_window_open(self):
        self.assertEqual(DeviceManager._smart_security(self.state(windows="OPEN")), "ATTENTION")

    def test_unknown_security(self):
        self.assertEqual(DeviceManager._smart_security(self.state(locked=None, doors="Unknown")), "UNKNOWN")

    def test_climate_modes(self):
        self.assertEqual(DeviceManager._smart_climate(self.state(heat="ON")), "HEATING")
        self.assertEqual(DeviceManager._smart_climate(self.state(vent="ON")), "VENTILATION")
        self.assertEqual(DeviceManager._smart_climate(self.state(ac="ON")), "CLIMATE")
        self.assertEqual(DeviceManager._smart_climate(self.state()), "OFF")

    def test_vehicle_state(self):
        self.assertEqual(DeviceManager._smart_vehicle_state(self.state()), "PARKED")


class DeviceModelTests(unittest.TestCase):
    def test_smart_units_exist(self):
        from constants import UNITS
        self.assertEqual(UNITS["vehicle_security"], 26)
        self.assertEqual(UNITS["climate_state"], 27)
        self.assertEqual(UNITS["data_quality"], 28)

    def test_all_units_are_contiguous(self):
        from constants import UNITS
        self.assertEqual(sorted(UNITS.values()), list(range(1, 45)))


class DistanceDeltaTests(unittest.TestCase):
    def test_distance_delta(self):
        previous = 7232.0
        current = 7236.5
        self.assertEqual(current - previous, 4.5)

    def test_negative_odometer_jump(self):
        self.assertLess(7230.0 - 7236.5, 0)


if __name__ == "__main__":
    unittest.main()


class DeviceTypeTests(unittest.TestCase):
    def test_custom_km_options(self):
        from devices import DeviceManager
        self.assertEqual(DeviceManager.CUSTOM_KM_OPTIONS, {"Custom": "1;km"})
        self.assertEqual(DeviceManager.CUSTOM_KM_TYPE, 243)
        self.assertEqual(DeviceManager.CUSTOM_KM_SUBTYPE, 31)
        self.assertEqual(DeviceManager.CUSTOM_KM_SWITCHTYPE, 0)



class TelemetryTests(unittest.TestCase):
    def test_extended_telemetry(self):
        data = {"vehicle": {
            "fuelStatus": {"primaryEngineRange": {"engineType": "GASOLINE", "currentFuelLevelInPercent": 100, "remainingRangeInKm": 640}},
            "charging": {"state": "NOT_CHARGING", "batteryLevelInPercent": 80, "remainingRangeInKm": 42, "connected": False, "targetStateOfChargeInPercent": 90, "mode": "MANUAL", "carCapturedTimestamp": "2026-09-05T07:00:00Z"},
            "odometer": {"mileageInKm": 7232, "carCapturedTimestamp": "2026-09-05T07:04:51Z"},
            "operations": [{"name": "startAuxiliaryHeating"}],
        }, "errors": [{"type": "https://example/_UNSUPPORTED", "code": "_UNSUPPORTED"}]}
        state = VehicleState.from_api(data)
        self.assertEqual(state.fuel_type, "GASOLINE")
        self.assertEqual(state.battery_soc, 80.0)
        self.assertEqual(state.electric_range, 42.0)
        self.assertFalse(state.charging_connected)
        self.assertEqual(state.charge_target, 90.0)
        self.assertEqual(state.supported_operations, ["startAuxiliaryHeating"])
        self.assertEqual(len(state.api_errors), 1)

    def test_new_units(self):
        from constants import UNITS
        self.assertEqual(UNITS["battery_soc"], 31)
        self.assertEqual(UNITS["supported_operations"], 41)
        self.assertEqual(UNITS["api_rate_remaining"], 42)
        self.assertEqual(UNITS["api_rate_reset"], 43)
        self.assertEqual(UNITS["api_key_status"], 44)
        self.assertEqual(sorted(UNITS.values()), list(range(1, 45)))


class NativeStateSensorTests(unittest.TestCase):
    def test_selector_definition(self):
        self.assertEqual(DeviceManager.SELECTOR_TYPE, 244)
        self.assertEqual(DeviceManager.SELECTOR_SUBTYPE, 62)
        self.assertEqual(DeviceManager.SELECTOR_SWITCHTYPE, 18)
        self.assertIn("LevelNames", DeviceManager.SELECTOR_OPTIONS["selector_open_closed"])

    def test_selector_levels(self):
        self.assertEqual(DeviceManager.SELECTOR_LEVELS["CLOSED"], 10)
        self.assertEqual(DeviceManager.SELECTOR_LEVELS["OPEN"], 20)
        self.assertEqual(DeviceManager.SELECTOR_LEVELS["LOCKED"], 10)
        self.assertEqual(DeviceManager.SELECTOR_LEVELS["UNLOCKED"], 20)

    def test_target_temperature_is_custom(self):
        self.assertEqual(DeviceManager.CUSTOM_C_OPTIONS, {"Custom": "1;°C"})


class DerivedTelemetryTests(unittest.TestCase):
    def test_api_status_mapping(self):
        from myskoda_api import APIResult
        from plugin import BasePlugin
        plugin = BasePlugin()
        self.assertEqual(plugin._api_status_text(APIResult(status=200)), "200 OK")
        self.assertIn("401 Unauthorized", plugin._api_status_text(APIResult(status=401)))
        self.assertIn("429 Too Many Requests", plugin._api_status_text(APIResult(status=429)))

    def test_api_key_warning_states(self):
        from datetime import timedelta, timezone, datetime
        from constants import API_KEY_EXPIRY_WARNING_DAYS
        from plugin import BasePlugin
        plugin = BasePlugin()
        now = datetime.now(timezone.utc).timestamp()
        ok = plugin._api_key_status(datetime.fromtimestamp(now + (API_KEY_EXPIRY_WARNING_DAYS + 1) * 86400, timezone.utc), now)
        warning = plugin._api_key_status(datetime.fromtimestamp(now + (API_KEY_EXPIRY_WARNING_DAYS - 1) * 86400, timezone.utc), now)
        expired = plugin._api_key_status(datetime.fromtimestamp(now - 60, timezone.utc), now)
        unknown = plugin._api_key_status(None, now)
        self.assertEqual((ok["level"], ok["state"]), (1, "OK"))
        self.assertEqual((warning["level"], warning["state"]), (2, "WARNING"))
        self.assertEqual((expired["level"], expired["state"]), (4, "EXPIRED"))
        self.assertEqual((unknown["level"], unknown["state"]), (0, "UNKNOWN"))

    def test_iso_timestamp_and_elapsed(self):
        from plugin import BasePlugin
        plugin = BasePlugin()
        dt = plugin._parse_iso_timestamp("2026-09-05T07:00:00Z")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.tzinfo.utcoffset(dt).total_seconds(), 0)
