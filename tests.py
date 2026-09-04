import unittest
from vehicle import parse_vehicle


class VehicleParserTests(unittest.TestCase):
    def test_parse_basic_vehicle(self):
        data = {"vehicle": {
            "name": "Octavia RS",
            "status": {"overall": {"doorsLocked": "YES", "doors": "CLOSED", "windows": "CLOSED", "lights": "OFF"}},
            "fuelStatus": {"primaryEngineRange": {"currentFuelLevelInPercent": 80, "remainingRangeInKm": 500}, "totalRangeInKm": 500},
            "odometer": {"mileageInKm": 12345},
            "parkingPosition": {"state": "PARKED", "gpsCoordinates": {"latitude": 49.5, "longitude": 6.1}},
        }}
        state = parse_vehicle(data)
        self.assertEqual(state.name, "Octavia RS")
        self.assertEqual(state.fuel_level, 80)
        self.assertEqual(state.odometer_km, 12345.0)
        self.assertEqual(state.parking_gps, "49.500000, 6.100000")

    def test_invalid_vehicle_is_rejected(self):
        self.assertIsNone(parse_vehicle({"vehicle": None}))

    def test_bad_coordinates_do_not_crash(self):
        state = parse_vehicle({"vehicle": {"parkingPosition": {"gpsCoordinates": {"latitude": "bad", "longitude": 1}}}})
        self.assertIsNone(state.parking_gps)


if __name__ == "__main__":
    unittest.main()
