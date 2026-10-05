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

    def test_charging_power_fields_v043(self):
        # NOTE: uses one of the 0.4.3-alpha candidate key sets as a stand-in.
        # Once verify_charging_fields.py confirms the real API keys for
        # your vehicle, update this fixture (and the candidate lists in
        # vehicle.py) to match - this test only guards the parsing wiring,
        # not the correctness of the guessed key names themselves.
        data = {"vehicle": {"charging": {
            "chargingPowerInKw": 11.0,
            "remainingTimeToFullyChargedInMinutes": 95,
            "chargeType": "AC",
        }}}
        state = VehicleState.from_api(data)
        self.assertEqual(state.charging_power, 11.0)
        self.assertEqual(state.remaining_charging_time, 95.0)
        self.assertEqual(state.charge_type, "AC")

    def test_phev_nested_charging_status_settings(self):
        # Regression test for the plug-in-hybrid Kodiaq GitHub issue: the real
        # API nests charging data under charging.status/charging.settings
        # instead of the flat keys the original 0.4.2 parsing assumed, which
        # left every EV-related device empty for hybrid vehicles.
        data = {"vehicle": {
            "charging": {
                "carCapturedTimestamp": "2026-09-17T17:45:16Z",
                "settings": {
                    "preferredChargeMode": "MANUAL",
                    "targetStateOfChargeInPercent": 80,
                },
                "status": {
                    "battery": {
                        "remainingCruisingRangeInMeters": 33000,
                        "stateOfChargeInPercent": 31,
                    },
                    "chargePowerInKw": 0.0,
                    "state": "CONNECT_CABLE",
                },
            },
            "fuelStatus": {
                "carType": "HYBRID",
                "primaryEngineRange": {"engineType": "GASOLINE", "currentFuelLevelInPercent": 100, "remainingRangeInKm": 650},
                "secondaryEngineRange": {"engineType": "ELECTRIC", "currentSoCInPercent": 31, "remainingRangeInKm": 33},
            },
        }}
        state = VehicleState.from_api(data)
        self.assertEqual(state.charging_state, "CONNECT_CABLE")
        self.assertEqual(state.battery_soc, 31.0)
        self.assertEqual(state.electric_range, 33.0)
        self.assertFalse(state.charging_connected)
        self.assertEqual(state.charge_target, 80.0)
        self.assertEqual(state.charge_mode, "MANUAL")
        self.assertEqual(state.charging_power, 0.0)
        self.assertEqual(state.remaining_charging_time, 0.0)

    def test_phev_ready_for_charging_resets_remaining_time(self):
        # Issue #9: third real dump from the same plug-in-hybrid Kodiaq,
        # captured right after a charge session ended. state is
        # READY_FOR_CHARGING, chargePowerInKw is explicitly 0.0, but
        # remainingTimeToFullyChargedInMinutes is entirely absent from the
        # response (unlike the CHARGING dump, where it was present). Without
        # the fix this device would stay stuck on its last real reading.
        data = {"vehicle": {"charging": {
            "isVehicleInSavedLocation": False,
            "carCapturedTimestamp": "2026-09-19T09:01:45Z",
            "settings": {
                "preferredChargeMode": "MANUAL",
                "targetStateOfChargeInPercent": 80,
            },
            "status": {
                "battery": {
                    "remainingCruisingRangeInMeters": 93000,
                    "stateOfChargeInPercent": 82,
                },
                "chargePowerInKw": 0.0,
                "state": "READY_FOR_CHARGING",
            },
        }}}
        state = VehicleState.from_api(data)
        self.assertEqual(state.charging_state, "READY_FOR_CHARGING")
        self.assertEqual(state.battery_soc, 82.0)
        self.assertEqual(state.electric_range, 93.0)
        self.assertTrue(state.charging_connected)
        self.assertEqual(state.charging_power, 0.0)
        self.assertEqual(state.remaining_charging_time, 0.0)

    def test_remaining_charging_time_not_guessed_on_unknown_state(self):
        # When there's no state key anywhere (raw_charge_state == ""), we
        # have no basis to reset remaining_charging_time - it should stay
        # None (and therefore untouched/stale in Domoticz) rather than being
        # guessed at 0.
        data = {"vehicle": {"charging": {"status": {"chargePowerInKw": 1.5}}}}
        state = VehicleState.from_api(data)
        self.assertIsNone(state.remaining_charging_time)

    def test_v110_plug_connection_state_preferred_over_derived_state(self):
        # v1.1.0 API release: plugConnectionState is the new authoritative
        # source for charging_connected. Use a derived state the fallback
        # heuristic would NOT otherwise recognize (an unknown/future value),
        # to prove plugConnectionState alone is enough - no reliance on the
        # derived-state fallback at all.
        data = {"vehicle": {"charging": {"status": {
            "state": "SOME_FUTURE_STATE",
            "plugConnectionState": "CONNECTED",
        }}}}
        state = VehicleState.from_api(data)
        self.assertTrue(state.charging_connected)

        data = {"vehicle": {"charging": {"status": {
            "state": "SOME_FUTURE_STATE",
            "plugConnectionState": "DISCONNECTED",
        }}}}
        state = VehicleState.from_api(data)
        self.assertFalse(state.charging_connected)

    def test_v110_plug_connection_state_absent_falls_back_to_derived_state(self):
        # plugConnectionState is optional per the API's own release notes;
        # when it's missing, the existing derived-state heuristic still
        # applies unchanged.
        data = {"vehicle": {"charging": {"status": {"state": "CONNECT_CABLE"}}}}
        state = VehicleState.from_api(data)
        self.assertFalse(state.charging_connected)

    def test_v110_plug_lock_state(self):
        data = {"vehicle": {"charging": {"status": {"plugLockState": "LOCKED"}}}}
        state = VehicleState.from_api(data)
        self.assertTrue(state.plug_lock_state)

        data = {"vehicle": {"charging": {"status": {"plugLockState": "UNLOCKED"}}}}
        state = VehicleState.from_api(data)
        self.assertFalse(state.plug_lock_state)

        # Optional field: absent means unknown, not guessed.
        data = {"vehicle": {"charging": {"status": {"chargePowerInKw": 1.0}}}}
        state = VehicleState.from_api(data)
        self.assertIsNone(state.plug_lock_state)

    def test_phev_electric_range_falls_back_to_fuel_status(self):
        # remainingCruisingRangeInMeters is only populated once charging.status
        # is present; fuelStatus.secondaryEngineRange is the hybrid-specific
        # fallback for electric range when it isn't.
        data = {"vehicle": {
            "charging": {"status": {"battery": {"stateOfChargeInPercent": 31}}},
            "fuelStatus": {"secondaryEngineRange": {"remainingRangeInKm": 33}},
        }}
        state = VehicleState.from_api(data)
        self.assertEqual(state.electric_range, 33.0)

    def test_phev_charging_active_confirms_remaining_time_and_connected(self):
        # Second real dump from the same plug-in-hybrid Kodiaq, this time
        # mid-charge. Confirms charging.status.remainingTimeToFullyChargedInMinutes
        # (previously only a guess) and that charging_connected can be safely
        # inferred True from a "CHARGING" state, alongside the earlier
        # "CONNECT_CABLE" -> False case.
        data = {"vehicle": {"charging": {
            "isVehicleInSavedLocation": False,
            "carCapturedTimestamp": "2026-09-18T18:09:35Z",
            "settings": {
                "preferredChargeMode": "MANUAL",
                "targetStateOfChargeInPercent": 80,
            },
            "status": {
                "battery": {
                    "remainingCruisingRangeInMeters": 49000,
                    "stateOfChargeInPercent": 41,
                },
                "chargePowerInKw": 10.0,
                "chargingRateInKilometersPerHour": 62.0,
                "fullyChargedAt": "2026-09-18T18:49:35Z",
                "remainingTimeToFullyChargedInMinutes": 40,
                "state": "CHARGING",
            },
        }}}
        state = VehicleState.from_api(data)
        self.assertEqual(state.charging_state, "CHARGING")
        self.assertEqual(state.battery_soc, 41.0)
        self.assertEqual(state.electric_range, 49.0)
        self.assertTrue(state.charging_connected)
        self.assertEqual(state.charge_target, 80.0)
        self.assertEqual(state.charge_mode, "MANUAL")
        self.assertEqual(state.charging_power, 10.0)
        self.assertEqual(state.remaining_charging_time, 40.0)

    def test_charging_power_fields_missing_default_safely(self):
        state = VehicleState.from_api({"vehicle": {"charging": {}}})
        self.assertIsNone(state.charging_power)
        self.assertIsNone(state.remaining_charging_time)
        self.assertEqual(state.charge_type, "Unknown")

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
        self.assertEqual(sorted(UNITS.values()), list(range(1, 52)))


class DistanceDeltaTests(unittest.TestCase):
    def test_distance_delta(self):
        previous = 7232.0
        current = 7236.5
        self.assertEqual(current - previous, 4.5)

    def test_negative_odometer_jump(self):
        self.assertLess(7230.0 - 7236.5, 0)



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

    def test_air_conditioning_active_derivation(self):
        # CONFIRMED against the real OpenAPI spec: AirConditioning.state is
        # an 8-value enum, not a simple on/off. air_conditioning_active
        # collapses it to a tri-state bool for the remote-control selector
        # (unit 49), without touching the raw air_conditioning text (unit 16).
        def ac_state_for(state_value):
            data = {"vehicle": {"airConditioning": {"state": state_value}}}
            return VehicleState.from_api(data)

        for value in ("COOLING", "HEATING", "HEATING_AUXILIARY", "VENTILATION"):
            state = ac_state_for(value)
            self.assertEqual(state.air_conditioning, value)
            self.assertIs(state.air_conditioning_active, True, "expected {} to be active".format(value))

        for value in ("OFF", "COMPLETED"):
            state = ac_state_for(value)
            self.assertEqual(state.air_conditioning, value)
            self.assertIs(state.air_conditioning_active, False, "expected {} to be inactive".format(value))

        for value in ("UNKNOWN", "UNSUPPORTED"):
            state = ac_state_for(value)
            self.assertIsNone(state.air_conditioning_active)

        # No airConditioning block at all - air_conditioning stays "Unknown",
        # air_conditioning_active must stay None rather than being guessed.
        no_ac_state = VehicleState.from_api({"vehicle": {}})
        self.assertEqual(no_ac_state.air_conditioning, "Unknown")
        self.assertIsNone(no_ac_state.air_conditioning_active)

    def test_active_ventilation_active_derivation(self):
        # CONFIRMED against the real spec: ActiveVentilation.state is OFF,
        # PREHEATING, VENTILATION, UNKNOWN or UNSUPPORTED.
        def vent_state_for(state_value):
            data = {"vehicle": {"activeVentilation": {"state": state_value}}}
            return VehicleState.from_api(data)

        for value in ("PREHEATING", "VENTILATION"):
            state = vent_state_for(value)
            self.assertEqual(state.active_ventilation, value)
            self.assertIs(state.active_ventilation_active, True, "expected {} to be active".format(value))

        state = vent_state_for("OFF")
        self.assertIs(state.active_ventilation_active, False)

        for value in ("UNKNOWN", "UNSUPPORTED"):
            state = vent_state_for(value)
            self.assertIsNone(state.active_ventilation_active)

        no_vent_state = VehicleState.from_api({"vehicle": {}})
        self.assertIsNone(no_vent_state.active_ventilation_active)

    def test_auxiliary_heating_active_derivation(self):
        # CONFIRMED against the real spec: AuxiliaryHeating.state is OFF,
        # PREHEATING, HEATING_AUXILIARY, VENTILATION, UNKNOWN or UNSUPPORTED.
        def heat_state_for(state_value):
            data = {"vehicle": {"auxiliaryHeating": {"state": state_value}}}
            return VehicleState.from_api(data)

        for value in ("PREHEATING", "HEATING_AUXILIARY", "VENTILATION"):
            state = heat_state_for(value)
            self.assertEqual(state.auxiliary_heating, value)
            self.assertIs(state.auxiliary_heating_active, True, "expected {} to be active".format(value))

        state = heat_state_for("OFF")
        self.assertIs(state.auxiliary_heating_active, False)

        for value in ("UNKNOWN", "UNSUPPORTED"):
            state = heat_state_for(value)
            self.assertIsNone(state.auxiliary_heating_active)

        no_heat_state = VehicleState.from_api({"vehicle": {}})
        self.assertIsNone(no_heat_state.auxiliary_heating_active)

    def test_new_units(self):
        from constants import UNITS
        self.assertEqual(UNITS["battery_soc"], 31)
        self.assertEqual(UNITS["supported_operations"], 41)
        self.assertEqual(UNITS["api_rate_remaining"], 42)
        self.assertEqual(UNITS["api_rate_reset"], 43)
        self.assertEqual(UNITS["api_key_status"], 44)
        self.assertEqual(UNITS["charging_power"], 45)
        self.assertEqual(UNITS["remaining_charging_time"], 46)
        self.assertEqual(UNITS["charge_type"], 47)
        self.assertEqual(UNITS["plug_lock_state"], 48)
        self.assertEqual(UNITS["air_conditioning_control"], 49)
        self.assertEqual(UNITS["active_ventilation_control"], 50)
        self.assertEqual(UNITS["auxiliary_heating_control"], 51)
        self.assertEqual(sorted(UNITS.values()), list(range(1, 52)))

    def test_writable_units(self):
        from constants import UNITS, WRITABLE_UNITS
        self.assertEqual(WRITABLE_UNITS, {
            UNITS["air_conditioning_control"],
            UNITS["active_ventilation_control"],
            UNITS["auxiliary_heating_control"],
        })


class DeviceManagerLoggingTests(unittest.TestCase):
    """A missing Domoticz device used to make every update to it vanish
    with no trace at all - exactly the kind of thing that makes a button
    click (or any other update) look like "nothing happens". These confirm
    it's now surfaced via the logger instead.
    """

    def test_update_to_missing_device_logs_error_instead_of_silently_doing_nothing(self):
        from unittest.mock import MagicMock
        logger = MagicMock()
        manager = DeviceManager(logger, {})  # no Domoticz devices at all
        manager.update_text("air_conditioning", "OFF")
        logger.Error.assert_called_once()
        self.assertIn("air_conditioning", str(logger.Error.call_args[0][0]))

    def test_update_to_existing_device_does_not_log_error(self):
        from unittest.mock import MagicMock
        from constants import UNITS
        logger = MagicMock()
        device = MagicMock()
        manager = DeviceManager(logger, {UNITS["air_conditioning"]: device})
        manager.update_text("air_conditioning", "OFF")
        logger.Error.assert_not_called()
        device.Update.assert_called_once()


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

    def test_active_text_maps_to_selector_on_off_range(self):
        # Regression test: syncing a *_control unit (selector_on_off mode -
        # LevelNames "Unknown|Off|On", levels 0/10/20) from a raw
        # multi-valued telemetry state (air_conditioning, auxiliary_heating,
        # active_ventilation) used to send levels like 30 (COOLING) or 40
        # (VENTILATION) straight through SELECTOR_LEVELS, which
        # selector_on_off's LevelNames doesn't cover. _active_text (shared
        # by all three *_control units) must collapse everything to
        # ON/OFF/UNKNOWN first.
        self.assertEqual(DeviceManager._active_text(True), "ON")
        self.assertEqual(DeviceManager._active_text(False), "OFF")
        self.assertEqual(DeviceManager._active_text(None), "UNKNOWN")
        for text in (DeviceManager._active_text(True), DeviceManager._active_text(False), DeviceManager._active_text(None)):
            level = DeviceManager.SELECTOR_LEVELS.get(text, 0)
            self.assertIn(level, (0, 10, 20), "level {} for {!r} is out of selector_on_off's range".format(level, text))


class DerivedTelemetryTests(unittest.TestCase):
    def test_api_status_mapping(self):
        from myskoda_api import APIResult
        from plugin import BasePlugin
        plugin = BasePlugin()
        self.assertEqual(plugin._api_status_text(APIResult(status=200)), "200 OK")
        self.assertIn("401 Unauthorized", plugin._api_status_text(APIResult(status=401)))
        self.assertIn("429 Too Many Requests", plugin._api_status_text(APIResult(status=429)))
        self.assertIn("rate-limit-exceeded", plugin._api_status_text(APIResult(status=429, problem_type="https://public.api.connect.skoda-auto.cz/problems/rate-limit-exceeded")))

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


class RemoteCommandTests(unittest.TestCase):
    """onCommand dispatch logic (plugin.py), new in 0.4.4.0. self.api and
    self.devices are replaced with MagicMocks so no real HTTP or Domoticz
    device call ever happens here - only the dispatch/gating logic itself is
    under test.
    """

    def _plugin_with_mocks(self, commands_enabled=True, api_ok=True, auxiliary_heating_pin="1234"):
        from unittest.mock import MagicMock
        from myskoda_api import APIResult
        from plugin import BasePlugin
        from vehicle import VehicleState

        plugin = BasePlugin()
        plugin.commands_enabled = commands_enabled
        plugin.auxiliary_heating_pin = auxiliary_heating_pin
        plugin.devices = MagicMock()
        plugin.cached_state = VehicleState()
        plugin.api = MagicMock()
        result = APIResult(
            ok=api_ok, status=200 if api_ok else 422,
            error="" if api_ok else "HTTP 422",
            problem_detail="" if api_ok else "unsupportedOperation",
        )
        plugin.api.start_air_conditioning.return_value = result
        plugin.api.stop_air_conditioning.return_value = result
        plugin.api.start_active_ventilation.return_value = result
        plugin.api.stop_active_ventilation.return_value = result
        plugin.api.start_auxiliary_heating.return_value = result
        plugin.api.stop_auxiliary_heating.return_value = result
        return plugin

    def test_start_command_calls_api_and_updates_selector_optimistically(self):
        from constants import UNITS
        plugin = self._plugin_with_mocks()
        plugin.onCommand(UNITS["air_conditioning_control"], "Set Level", 20, 0)
        plugin.api.start_air_conditioning.assert_called_once()
        plugin.api.stop_air_conditioning.assert_not_called()
        plugin.devices._update_selector.assert_called_once_with("air_conditioning_control", "ON")
        plugin.devices.restore_selector.assert_not_called()

    def test_stop_command_calls_api_and_updates_selector_optimistically(self):
        from constants import UNITS
        plugin = self._plugin_with_mocks()
        plugin.onCommand(UNITS["air_conditioning_control"], "Set Level", 10, 0)
        plugin.api.stop_air_conditioning.assert_called_once()
        plugin.api.start_air_conditioning.assert_not_called()
        plugin.devices._update_selector.assert_called_once_with("air_conditioning_control", "OFF")

    def test_commands_disabled_by_default_setting_blocks_api_call(self):
        from constants import UNITS
        plugin = self._plugin_with_mocks(commands_enabled=False)
        plugin.onCommand(UNITS["air_conditioning_control"], "Set Level", 20, 0)
        plugin.api.start_air_conditioning.assert_not_called()
        plugin.devices.restore_selector.assert_called_once_with(UNITS["air_conditioning_control"], plugin.cached_state)

    def test_api_failure_restores_selector_instead_of_sticking(self):
        from constants import UNITS
        plugin = self._plugin_with_mocks(api_ok=False)
        plugin.onCommand(UNITS["air_conditioning_control"], "Set Level", 20, 0)
        plugin.api.start_air_conditioning.assert_called_once()
        plugin.devices._update_selector.assert_not_called()
        plugin.devices.restore_selector.assert_called_once_with(UNITS["air_conditioning_control"], plugin.cached_state)

    def test_other_units_are_unaffected_read_only_behavior(self):
        from constants import UNITS
        plugin = self._plugin_with_mocks()
        plugin.onCommand(UNITS["lights"], "Set Level", 20, 0)
        plugin.api.start_air_conditioning.assert_not_called()
        plugin.api.stop_air_conditioning.assert_not_called()
        plugin.devices.restore_selector.assert_called_once_with(UNITS["lights"], plugin.cached_state)

    def test_active_ventilation_start_command_calls_api_and_updates_selector_optimistically(self):
        from constants import UNITS
        plugin = self._plugin_with_mocks()
        plugin.onCommand(UNITS["active_ventilation_control"], "Set Level", 20, 0)
        plugin.api.start_active_ventilation.assert_called_once_with()
        plugin.api.stop_active_ventilation.assert_not_called()
        plugin.devices._update_selector.assert_called_once_with("active_ventilation_control", "ON")
        plugin.devices.restore_selector.assert_not_called()

    def test_active_ventilation_stop_command_calls_api_and_updates_selector_optimistically(self):
        from constants import UNITS
        plugin = self._plugin_with_mocks()
        plugin.onCommand(UNITS["active_ventilation_control"], "Set Level", 10, 0)
        plugin.api.stop_active_ventilation.assert_called_once_with()
        plugin.api.start_active_ventilation.assert_not_called()
        plugin.devices._update_selector.assert_called_once_with("active_ventilation_control", "OFF")

    def test_active_ventilation_command_blocked_when_commands_disabled(self):
        from constants import UNITS
        plugin = self._plugin_with_mocks(commands_enabled=False)
        plugin.onCommand(UNITS["active_ventilation_control"], "Set Level", 20, 0)
        plugin.api.start_active_ventilation.assert_not_called()
        plugin.devices.restore_selector.assert_called_once_with(UNITS["active_ventilation_control"], plugin.cached_state)

    def test_auxiliary_heating_start_command_sends_the_configured_pin(self):
        from constants import UNITS
        plugin = self._plugin_with_mocks(auxiliary_heating_pin="9876")
        plugin.onCommand(UNITS["auxiliary_heating_control"], "Set Level", 20, 0)
        plugin.api.start_auxiliary_heating.assert_called_once_with("9876")
        plugin.devices._update_selector.assert_called_once_with("auxiliary_heating_control", "ON")
        plugin.devices.restore_selector.assert_not_called()

    def test_auxiliary_heating_stop_command_does_not_require_a_pin(self):
        # Per the real spec, stopping auxiliary heating needs no PIN at all
        # - only starting it does.
        from constants import UNITS
        plugin = self._plugin_with_mocks(auxiliary_heating_pin="")
        plugin.onCommand(UNITS["auxiliary_heating_control"], "Set Level", 10, 0)
        plugin.api.stop_auxiliary_heating.assert_called_once_with()
        plugin.devices._update_selector.assert_called_once_with("auxiliary_heating_control", "OFF")
        plugin.devices.restore_selector.assert_not_called()

    def test_auxiliary_heating_start_command_blocked_without_a_configured_pin(self):
        from constants import UNITS
        plugin = self._plugin_with_mocks(auxiliary_heating_pin="")
        plugin.onCommand(UNITS["auxiliary_heating_control"], "Set Level", 20, 0)
        plugin.api.start_auxiliary_heating.assert_not_called()
        plugin.devices.restore_selector.assert_called_once_with(UNITS["auxiliary_heating_control"], plugin.cached_state)

    def test_auxiliary_heating_command_blocked_when_commands_disabled_even_with_pin_set(self):
        from constants import UNITS
        plugin = self._plugin_with_mocks(commands_enabled=False, auxiliary_heating_pin="9876")
        plugin.onCommand(UNITS["auxiliary_heating_control"], "Set Level", 20, 0)
        plugin.api.start_auxiliary_heating.assert_not_called()
        plugin.devices.restore_selector.assert_called_once_with(UNITS["auxiliary_heating_control"], plugin.cached_state)

    def test_successful_command_updates_rate_limit_bookkeeping(self):
        # The real spec confirms command responses (202 Accepted) carry the
        # same RateLimit-*/X-API-Key-Expires-At headers as the main poll, so
        # a command call must update the same bookkeeping _poll() does, not
        # just the main GET path.
        from constants import UNITS
        from myskoda_api import APIResult
        plugin = self._plugin_with_mocks()
        plugin.api.start_air_conditioning.return_value = APIResult(
            ok=True, status=202, headers={
                "ratelimit-remaining": "17",
                "ratelimit-reset": "120",
                "x-api-key-expires-at": "2027-01-01T00:00:00Z",
            },
        )
        self.assertIsNone(plugin.rate_remaining)
        plugin.onCommand(UNITS["air_conditioning_control"], "Set Level", 20, 0)
        self.assertEqual(plugin.rate_remaining, 17)
        self.assertEqual(plugin.api_key_expiry, "2027-01-01T00:00:00Z")
        self.assertIsNotNone(plugin.rate_reset_at)

    def test_failed_command_still_updates_rate_limit_bookkeeping(self):
        # Headers are present on error responses too (confirmed in the
        # spec's 403/422 response definitions), so bookkeeping must be
        # updated on the failure path as well, not only on success.
        from constants import UNITS
        from myskoda_api import APIResult
        plugin = self._plugin_with_mocks(api_ok=False)
        plugin.api.start_air_conditioning.return_value = APIResult(
            ok=False, status=422, error="HTTP 422",
            problem_type="https://public.api.connect.skoda-auto.cz/problems/operation-not-supported",
            problem_detail="The vehicle does not support this operation.",
            headers={"ratelimit-remaining": "16"},
        )
        plugin.onCommand(UNITS["air_conditioning_control"], "Set Level", 20, 0)
        self.assertEqual(plugin.rate_remaining, 16)

    def test_oncommand_logs_receipt_unconditionally(self):
        # Reported symptom: "I push the button in Domoticz and nothing
        # happens". This line fires on every single onCommand call,
        # regardless of the Debug setting, so it is the first thing to check
        # in the Domoticz Log - if it's missing after a click, Domoticz
        # itself never called the plugin.
        from unittest.mock import MagicMock
        from constants import UNITS
        plugin = self._plugin_with_mocks()
        plugin.logger = MagicMock()
        plugin.onCommand(UNITS["air_conditioning_control"], "Set Level", 20, 0)
        logged = [str(c.args[0]) for c in plugin.logger.Log.call_args_list]
        self.assertTrue(any("onCommand received" in m and "unit=" in m for m in logged))

    def test_oncommand_catches_and_logs_unexpected_exceptions(self):
        # A crash anywhere in the dispatch chain must be visible in the
        # Domoticz log, never silently swallowed - that would also look
        # exactly like "nothing happens".
        from unittest.mock import MagicMock
        from constants import UNITS
        plugin = self._plugin_with_mocks()
        plugin.logger = MagicMock()
        plugin.devices.restore_selector.side_effect = RuntimeError("boom")
        plugin.onCommand(UNITS["lights"], "Set Level", 20, 0)
        plugin.logger.Error.assert_called_once()
        self.assertIn("boom", str(plugin.logger.Error.call_args[0][0]))

    def test_restore_without_cached_state_logs_instead_of_silently_doing_nothing(self):
        # Before any successful poll, there is no cached state to revert
        # to - the selector is simply left where the user clicked it. That
        # is indistinguishable from "nothing happens" in the Domoticz UI
        # without this log line.
        from unittest.mock import MagicMock
        from constants import UNITS
        plugin = self._plugin_with_mocks(commands_enabled=False)
        plugin.cached_state = None
        plugin.logger = MagicMock()
        plugin.onCommand(UNITS["air_conditioning_control"], "Set Level", 20, 0)
        plugin.devices.restore_selector.assert_not_called()
        logged = [str(c.args[0]) for c in plugin.logger.Log.call_args_list]
        self.assertTrue(any("no cached vehicle state" in m for m in logged))


class MySkodaCommandTests(unittest.TestCase):
    """Verifies the actual outgoing HTTP request shape for the new command
    methods (method, URL, headers, body) without making a real network call.
    """

    @staticmethod
    def _fake_urlopen(captured, status=200, body=b""):
        from unittest.mock import MagicMock

        def _urlopen(request, timeout=None):
            captured["url"] = request.full_url
            captured["method"] = request.get_method()
            captured["data"] = request.data
            captured["headers"] = {k.lower(): v for k, v in request.header_items()}
            response = MagicMock()
            response.status = status
            response.headers = {}
            response.read.return_value = body
            response.__enter__.return_value = response
            response.__exit__.return_value = False
            return response

        return _urlopen

    def test_start_air_conditioning_request_shape(self):
        import json
        from unittest.mock import patch
        import constants
        from myskoda_api import MySkodaAPI

        api = MySkodaAPI("testkey", "TESTVIN123")
        captured = {}
        with patch("myskoda_api.urllib.request.urlopen", side_effect=self._fake_urlopen(captured)):
            result = api.start_air_conditioning(22.5)

        self.assertTrue(result.ok)
        self.assertEqual(captured["method"], "POST")
        self.assertEqual(captured["url"], constants.API_BASE + "/api/v1/vehicles/TESTVIN123/air-conditioning/start")
        self.assertEqual(captured["headers"].get("x-api-key"), "testkey")
        self.assertEqual(captured["headers"].get("content-type"), "application/json")
        sent_body = json.loads(captured["data"].decode("utf-8"))
        self.assertEqual(sent_body, {"targetTemperature": {"value": 22.5, "unit": "CELSIUS"}})

    def test_start_air_conditioning_without_temperature_sends_empty_body(self):
        # The real OpenAPI spec marks this endpoint's requestBody as
        # required: true, so omitting the body entirely is not valid - an
        # empty {} is the correct request when no target temperature is
        # given (confirmed against myskoda-public-api.yaml v1.1.0).
        import json
        from unittest.mock import patch
        from myskoda_api import MySkodaAPI

        api = MySkodaAPI("testkey", "TESTVIN123")
        captured = {}
        with patch("myskoda_api.urllib.request.urlopen", side_effect=self._fake_urlopen(captured)):
            result = api.start_air_conditioning()

        self.assertTrue(result.ok)
        self.assertEqual(json.loads(captured["data"].decode("utf-8")), {})
        self.assertEqual(captured["headers"].get("content-type"), "application/json")

    def test_stop_air_conditioning_request_shape(self):
        from unittest.mock import patch
        import constants
        from myskoda_api import MySkodaAPI

        api = MySkodaAPI("testkey", "TESTVIN123")
        captured = {}
        with patch("myskoda_api.urllib.request.urlopen", side_effect=self._fake_urlopen(captured)):
            result = api.stop_air_conditioning()

        self.assertTrue(result.ok)
        self.assertEqual(captured["method"], "POST")
        self.assertEqual(captured["url"], constants.API_BASE + "/api/v1/vehicles/TESTVIN123/air-conditioning/stop")
        self.assertIsNone(captured["data"])
        self.assertNotIn("content-type", captured["headers"])

    def test_start_active_ventilation_request_shape(self):
        # Per the real spec, neither active-ventilation endpoint takes a
        # request body at all (unlike air-conditioning/start).
        from unittest.mock import patch
        import constants
        from myskoda_api import MySkodaAPI

        api = MySkodaAPI("testkey", "TESTVIN123")
        captured = {}
        with patch("myskoda_api.urllib.request.urlopen", side_effect=self._fake_urlopen(captured)):
            result = api.start_active_ventilation()

        self.assertTrue(result.ok)
        self.assertEqual(captured["method"], "POST")
        self.assertEqual(captured["url"], constants.API_BASE + "/api/v1/vehicles/TESTVIN123/active-ventilation/start")
        self.assertIsNone(captured["data"])
        self.assertNotIn("content-type", captured["headers"])

    def test_stop_active_ventilation_request_shape(self):
        from unittest.mock import patch
        import constants
        from myskoda_api import MySkodaAPI

        api = MySkodaAPI("testkey", "TESTVIN123")
        captured = {}
        with patch("myskoda_api.urllib.request.urlopen", side_effect=self._fake_urlopen(captured)):
            result = api.stop_active_ventilation()

        self.assertTrue(result.ok)
        self.assertEqual(captured["method"], "POST")
        self.assertEqual(captured["url"], constants.API_BASE + "/api/v1/vehicles/TESTVIN123/active-ventilation/stop")
        self.assertIsNone(captured["data"])

    def test_start_auxiliary_heating_sends_spin_and_nothing_else(self):
        # Per the real spec, "spin" (the vehicle's Security PIN) is the only
        # required field on StartAuxiliaryHeatingConfiguration - this
        # plugin doesn't set targetTemperature/durationInSeconds/startMode.
        import json
        from unittest.mock import patch
        import constants
        from myskoda_api import MySkodaAPI

        api = MySkodaAPI("testkey", "TESTVIN123")
        captured = {}
        with patch("myskoda_api.urllib.request.urlopen", side_effect=self._fake_urlopen(captured)):
            result = api.start_auxiliary_heating("1234")

        self.assertTrue(result.ok)
        self.assertEqual(captured["method"], "POST")
        self.assertEqual(captured["url"], constants.API_BASE + "/api/v1/vehicles/TESTVIN123/auxiliary-heating/start")
        self.assertEqual(captured["headers"].get("content-type"), "application/json")
        self.assertEqual(json.loads(captured["data"].decode("utf-8")), {"spin": "1234"})

    def test_start_auxiliary_heating_never_logs_the_pin(self):
        # The PIN is a credential like the API key - it must never appear
        # in a log line, even at Debug level.
        from unittest.mock import MagicMock, patch
        from myskoda_api import MySkodaAPI

        logger = MagicMock()
        api = MySkodaAPI("testkey", "TESTVIN123", logger)
        captured = {}
        with patch("myskoda_api.urllib.request.urlopen", side_effect=self._fake_urlopen(captured)):
            api.start_auxiliary_heating("SECRET-PIN-4242")

        logged_text = " ".join(str(c.args[0]) for c in logger.Debug.call_args_list)
        self.assertNotIn("SECRET-PIN-4242", logged_text)

    def test_stop_auxiliary_heating_request_shape(self):
        from unittest.mock import patch
        import constants
        from myskoda_api import MySkodaAPI

        api = MySkodaAPI("testkey", "TESTVIN123")
        captured = {}
        with patch("myskoda_api.urllib.request.urlopen", side_effect=self._fake_urlopen(captured)):
            result = api.stop_auxiliary_heating()

        self.assertTrue(result.ok)
        self.assertEqual(captured["method"], "POST")
        self.assertEqual(captured["url"], constants.API_BASE + "/api/v1/vehicles/TESTVIN123/auxiliary-heating/stop")
        self.assertIsNone(captured["data"])

    def test_command_http_error_is_reported_not_raised(self):
        from unittest.mock import patch
        import urllib.error
        from myskoda_api import MySkodaAPI

        api = MySkodaAPI("testkey", "TESTVIN123")

        def _raise(request, timeout=None):
            raise urllib.error.HTTPError(
                request.full_url, 422, "Unprocessable",
                {"Content-Type": "application/problem+json"},
                None,
            )

        with patch("myskoda_api.urllib.request.urlopen", side_effect=_raise):
            result = api.start_air_conditioning()

        self.assertFalse(result.ok)
        self.assertEqual(result.status, 422)


if __name__ == "__main__":
    unittest.main()
