import unittest

from myskoda_api import APIResult
from vehicle import VehicleState


class VehicleParserTests(unittest.TestCase):
    def test_current_api_vehicle_wrapper(self):
        data = {
            "vehicle": {
                "auxiliaryHeating": {
                    "state": "OFF",
                    "targetTemperature": {"value": 21.0, "unit": "CELSIUS"},
                },
                "fuelStatus": {
                    "carType": "GASOLINE",
                    "primaryEngineRange": {
                        "currentFuelLevelInPercent": 100,
                        "currentSoCInPercent": 100,
                        "engineType": "GASOLINE",
                        "remainingRangeInKm": 640,
                    },
                    "totalRangeInKm": 640,
                },
                "licensePlate": "TEST",
                "name": "Octavia RS",
                "odometer": {"mileageInKm": 7232, "carCapturedTimestamp": "2026-09-05T07:04:51Z"},
                "parkingPosition": {
                    "state": "PARKED",
                    "formattedAddress": "Luxembourg",
                    "gpsCoordinates": {"latitude": 49.6, "longitude": 6.1},
                },
                "status": {
                    "overall": {
                        "doorsLocked": "YES",
                        "locked": "YES",
                        "doors": "CLOSED",
                        "windows": "OPEN",
                        "lights": "OFF",
                    },
                    "detail": {"sunroof": "CLOSED", "trunk": "CLOSED", "bonnet": "CLOSED"},
                    "carCapturedTimestamp": "2026-09-05T07:04:51Z",
                },
                "vin": "TESTVIN",
            }
        }
        state = VehicleState.from_api(data)
        self.assertEqual(state.vin, "TESTVIN")
        self.assertEqual(state.name, "Octavia RS")
        self.assertEqual(state.license_plate, "TEST")
        self.assertTrue(state.doors_locked)
        self.assertEqual(state.windows, "OPEN")
        self.assertEqual(state.fuel_level, 100.0)
        self.assertEqual(state.fuel_range, 640.0)
        self.assertEqual(state.total_range, 640.0)
        self.assertEqual(state.odometer, 7232.0)
        self.assertEqual(state.parking_state, "PARKED")
        self.assertAlmostEqual(state.parking_latitude, 49.6)
        self.assertEqual(state.target_temperature, 21.0)

    def test_legacy_flat_vehicle_is_still_supported(self):
        data = {
            "info": {"vin": "WVWTEST", "name": "Octavia RS", "licensePlate": "L-TEST"},
            "status": {"doorsLocked": True, "doors": "closed", "windows": "closed", "lights": "off", "trunk": "closed", "vehicleState": "PARKED"},
            "fuelStatus": {"fuelLevel": 55, "fuelRange": 420, "totalRange": 600},
            "odometer": {"value": 12345},
            "parkingPosition": {"address": "Luxembourg", "latitude": 49.6116, "longitude": 6.1319},
        }
        state = VehicleState.from_api(data)
        self.assertEqual(state.name, "Octavia RS")
        self.assertTrue(state.doors_locked)
        self.assertEqual(state.fuel_level, 55.0)
        self.assertEqual(state.odometer, 12345.0)

    def test_missing_fields_are_safe(self):
        state = VehicleState.from_api({"vehicle": {"name": "Car"}})
        self.assertEqual(state.name, "Car")
        self.assertIsNone(state.fuel_level)
        self.assertEqual(state.doors, "Unknown")

    def test_rate_limit_and_expiry_headers(self):
        result = APIResult(headers={
            "ratelimit-limit": "20",
            "ratelimit-remaining": "15",
            "ratelimit-reset": "873",
            "x-api-key-expires-at": "2027-03-04T13:44:43.043Z",
        })
        self.assertIn("limit=20", result.rate_text)
        self.assertIn("remaining=15", result.rate_text)
        self.assertIn("reset=873s", result.rate_text)
        self.assertEqual(result.api_key_expires_at, "2027-03-04T13:44:43.043Z")


if __name__ == "__main__":
    unittest.main()
