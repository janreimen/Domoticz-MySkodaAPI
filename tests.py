import unittest

from myskoda_api import APIResult
from vehicle import VehicleState


class VehicleParserTests(unittest.TestCase):
    def test_basic_vehicle(self):
        data = {
            "info": {"vin": "WVWTEST", "name": "Octavia RS", "licensePlate": "L-TEST"},
            "status": {"doorsLocked": True, "doors": "closed", "windows": "closed", "lights": "off", "trunk": "closed", "vehicleState": "PARKED"},
            "fuelStatus": {"fuelLevel": 55, "fuelRange": 420, "totalRange": 600},
            "odometer": {"value": 12345},
            "parkingPosition": {"address": "Luxembourg", "latitude": 49.6116, "longitude": 6.1319},
            "airConditioning": {"state": "inactive", "targetTemperature": 21},
            "auxiliaryHeating": {"state": "inactive"},
            "activeVentilation": {"state": "inactive"},
        }
        state = VehicleState.from_api(data)
        self.assertEqual(state.vin, "WVWTEST")
        self.assertEqual(state.name, "Octavia RS")
        self.assertTrue(state.doors_locked)
        self.assertEqual(state.fuel_level, 55.0)
        self.assertEqual(state.odometer, 12345.0)
        self.assertAlmostEqual(state.parking_latitude, 49.6116)

    def test_missing_fields_are_safe(self):
        state = VehicleState.from_api({"info": {"name": "Car"}})
        self.assertEqual(state.name, "Car")
        self.assertIsNone(state.fuel_level)
        self.assertEqual(state.doors, "Unknown")

    def test_rate_limit_text(self):
        result = APIResult(headers={"x-ratelimit-limit": "100", "x-ratelimit-remaining": "97"}, retry_after=4)
        self.assertIn("limit=100", result.rate_text)
        self.assertIn("remaining=97", result.rate_text)
        self.assertIn("retry-after=4", result.rate_text)


if __name__ == "__main__":
    unittest.main()
