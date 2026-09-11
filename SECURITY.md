# Security Policy

## Supported versions

Security fixes are intended for the current development/release version.

The current release is **0.4.2**. Older alpha releases may no longer receive security fixes; upgrading to the latest release is recommended.

## Reporting a vulnerability

Please do **not** publish API keys, credentials, VINs, private vehicle data, or exploitable security details in a public GitHub issue.

Use GitHub's private security reporting mechanism for the repository where available, or contact the maintainer privately.

Provide enough information to reproduce the issue without exposing secrets or private vehicle information.

## API keys and private data

The MySkoda API key is configured through the Domoticz hardware configuration and is marked as a password field by the plugin.

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

## Read-only design

The plugin is intentionally read-only. It retrieves vehicle telemetry and does not intentionally implement remote vehicle-control operations.

## Transport and dependencies

Communication with the MySkoda API uses HTTPS. Do not disable TLS certificate verification as a workaround for connectivity problems.

The plugin itself uses the Python standard library and does not require third-party Python packages.


## Supported versions

Security fixes are intended for the current development release.

## Reporting a vulnerability

Please do not publish API keys, credentials, VINs, or other private vehicle data in a public GitHub issue.

Use the repository's private GitHub security reporting mechanism where available, or contact the maintainer privately.

## API keys

The MySkoda API key is supplied through the Domoticz hardware configuration. The plugin does not intentionally log the API key and does not write it to its persistent state cache.

Users should still protect the Domoticz configuration and host filesystem because the API key is required for the integration to operate.

