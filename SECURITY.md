# Security Policy

## Supported versions

Security fixes are intended for the current development release.

## Reporting a vulnerability

Please do not publish API keys, credentials, VINs, or other private vehicle data in a public GitHub issue.

Use the repository's private GitHub security reporting mechanism where available, or contact the maintainer privately.

## API keys

The MySkoda API key is supplied through the Domoticz hardware configuration. The plugin does not intentionally log the API key and does not write it to its persistent state cache.

Users should still protect the Domoticz configuration and host filesystem because the API key is required for the integration to operate.
