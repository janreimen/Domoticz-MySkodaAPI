# Security Policy

## Supported versions

Security fixes are intended for the current development/release version.

The following versions of this project are actively supported with security updates:

- **0.4. **: ✅ Supported
- **< 0.3**: ❌ Not Supported

The current release is **0.4.4.1**. Older alpha releases may no longer receive security fixes; upgrading to the latest release is recommended.

## Reporting a vulnerability

Please do **not** publish API keys, credentials, VINs, private vehicle data, or exploitable security details in a public GitHub issue.

Use GitHub's private security reporting mechanism for the repository where available, or contact the maintainer privately.

Provide enough information to reproduce the issue without exposing secrets or private vehicle information.

## API keys and private data

The MySkoda API key is configured through the Domoticz hardware configuration and is marked as a password field by the plugin.

As of **0.4.4.002**, starting Auxiliary Heating Control (unit 51) also requires the vehicle's own Security PIN ("S-PIN"), configured through the same hardware screen (Mode5, also a password field). Like the API key, the PIN is never intentionally logged - at any Debug level - and is never written to the persistent vehicle-state or distance-state cache; a dedicated regression test asserts a representative PIN value never appears in any debug log call.

The plugin does not intentionally log the API key and does not write the API key to its persistent vehicle-state or distance-state cache.

Protect the following as sensitive configuration/data:

- Domoticz hardware configuration.
- Domoticz database and backups.
- The plugin directory and host filesystem.
- Logs and diagnostic exports.
- VINs and vehicle telemetry.

## Repository hygiene

The following files/directories are runtime or local-development material and must not be committed:

```text
myskoda_last_state.json
myskoda_distance_state.json
*_state.json
*.state.json
__pycache__/
*.py[cod]
.pytest_cache/
*.swp
*.swo
```

The repository `.gitignore` is configured to prevent accidental publication of these files.

Never commit API keys, credentials, private vehicle data, or logs containing such information.

If a secret is accidentally committed, deleting the file in a later commit is insufficient. Rotate/revoke the exposed credential first, then remove the secret from the Git history.

## Remote commands

Vehicle telemetry is always read-only. As of **0.4.4.0** / **0.4.4.002**, the plugin can additionally send three remote vehicle commands (Air Conditioning, Active Ventilation and Auxiliary Heating Control) - but only when the **Enable Remote Commands** hardware setting (Mode4) is explicitly switched On. It is **Off by default**, so a fresh or upgraded installation stays command-free until the user opts in.

With commands enabled, each is still bounded:

- Every command call goes through the same enabled-check, API-readiness check, and (for starting Auxiliary Heating) PIN check before anything is sent.
- A failed command (non-2xx, including a vehicle-capability rejection or a rate limit) reverts the Domoticz selector to the last known cached state rather than leaving it stuck on a command that didn't actually happen.
- Command responses are retried and rate-limit-tracked the same way the main telemetry poll is.

## Transport and dependencies

Communication with the MySkoda API uses HTTPS. Do not disable TLS certificate verification as a workaround for connectivity problems.

The plugin itself uses the Python standard library and does not require third-party Python packages.

