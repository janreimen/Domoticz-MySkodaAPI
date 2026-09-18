#!/usr/bin/env python3
"""One-off verification tool for the 0.4.3-alpha charging-field candidates.

Runs completely outside Domoticz - only imports myskoda_api.py, which has
no Domoticz dependency. Use it once to confirm the real JSON keys for
charging power / remaining time / charge type before trusting the
candidate key lists added to vehicle.py in the 0.4.3-alpha patch.

Usage:
    python3 verify_charging_fields.py <API_KEY> <VIN>

or via environment variables:
    MYSKODA_API_KEY=... MYSKODA_VIN=... python3 verify_charging_fields.py

This counts as one request against your 20/hour rate limit - the same
quota the plugin itself uses, since it hits the same endpoint.
"""
import json
import os
import sys

from myskoda_api import MySkodaAPI


def main():
    api_key = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("MYSKODA_API_KEY")
    vin = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("MYSKODA_VIN")

    if not api_key or not vin:
        print("Usage: python3 verify_charging_fields.py <API_KEY> <VIN>", file=sys.stderr)
        print("(or set MYSKODA_API_KEY / MYSKODA_VIN)", file=sys.stderr)
        sys.exit(1)

    api = MySkodaAPI(api_key, vin)
    result = api.fetch_vehicle()

    print("--- request result ---")
    print("ok:", result.ok, "status:", result.status, "error:", result.error)
    print("rate:", result.rate_text)
    print()

    if not result.ok:
        print("Request failed - nothing to inspect.", file=sys.stderr)
        sys.exit(1)

    root = result.data.get("vehicle") if isinstance(result.data, dict) else None
    if not isinstance(root, dict):
        root = result.data if isinstance(result.data, dict) else {}

    charging = root.get("charging") or {}
    fuel = root.get("fuelStatus") or root.get("fuel_status") or {}

    print("--- full 'charging' object (this is what vehicle.py parses) ---")
    print(json.dumps(charging, indent=2, ensure_ascii=False))
    print()

    secondary = fuel.get("secondaryEngineRange")
    if secondary:
        # Present on plug-in hybrids; vehicle.py falls back to this for
        # electric_range when charging.status.battery isn't populated.
        print("--- fuelStatus.secondaryEngineRange (hybrid electric-range fallback) ---")
        print(json.dumps(secondary, indent=2, ensure_ascii=False))
        print()

    print("--- candidate key check against vehicle.py's current lookups ---")
    # Keep this in sync with the `first(charging, ...)` candidate lists in
    # vehicle.py's from_api(). Confirmed as of 2026-09-17 against a real
    # plug-in-hybrid Kodiaq dump: charging_state, battery_soc, electric_range
    # (via status.battery.remainingCruisingRangeInMeters, in meters),
    # charge_target and charge_mode all live under charging.status /
    # charging.settings. remaining_charging_time and charge_type below are
    # still unconfirmed best guesses - that dump was cut off before reaching
    # them, so treat any match here as a hint to verify, not a certainty.
    candidates = {
        "charging_power": ["status.chargePowerInKw", "chargePowerInKw", "chargingPowerInKw", "chargingPowerInKW", "powerInKw", "chargingPower"],
        "remaining_charging_time": ["status.remainingTimeToFullyChargedInMinutes", "remainingTimeToFullyChargedInMinutes", "remainingChargingTimeInMinutes", "remainingChargingTime"],
        "charge_type": ["status.chargeType", "status.chargingType", "chargeType", "type", "chargingType"],
    }

    def lookup(data, path):
        current = data
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                return False, None
            current = current[part]
        return True, current

    any_match = False
    for field, keys in candidates.items():
        found = []
        for key in keys:
            matched, value = lookup(charging, key)
            if matched:
                found.append((key, value))
        if found:
            any_match = True
            print("{}: MATCH on {}".format(field, found))
        else:
            print("{}: NO MATCH among {} - inspect the full object above for the real key".format(field, keys))

    if not any_match:
        print()
        print("None of the candidates matched. Look through the full object printed")
        print("above, find the real keys, and add them (as dotted paths if nested) to")
        print("the candidate lists in vehicle.py's from_api() - append, don't replace -")
        print("before relying on them in production.")


if __name__ == "__main__":
    main()

