#!/usr/bin/env python3
"""One-off verification tool for the 0.4.3 charging-field candidates.

Runs completely outside Domoticz - only imports myskoda_api.py, which has
no Domoticz dependency. Use it once to confirm the real JSON keys for
charging power / remaining time / charge type before trusting the
candidate key lists added to vehicle.py in the 0.4.3 patch.

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

    print("--- full 'charging' object (this is what vehicle.py parses) ---")
    print(json.dumps(charging, indent=2, ensure_ascii=False))
    print()

    print("--- candidate key check against vehicle.py's 0.4.3 lookups ---")
    candidates = {
        "charging_power": ["chargingPowerInKw", "chargingPowerInKW", "powerInKw", "chargingPower"],
        "remaining_charging_time": ["remainingTimeToFullyChargedInMinutes", "remainingChargingTimeInMinutes", "remainingChargingTime"],
        "charge_type": ["chargeType", "type", "chargingType"],
    }
    for field, keys in candidates.items():
        found = [k for k in keys if k in charging]
        if found:
            print("{}: MATCH on {} -> {}".format(field, found, [charging[k] for k in found]))
        else:
            print("{}: NO MATCH among {} - inspect the full object above for the real key".format(field, keys))

    if not any(k in charging for keys in candidates.values() for k in keys):
        print()
        print("None of the candidates matched. Look through the full object printed")
        print("above, find the real keys, and add them to the candidate lists in")
        print("vehicle.py (append, don't replace) before relying on the 0.4.3 patch.")


if __name__ == "__main__":
    main()

