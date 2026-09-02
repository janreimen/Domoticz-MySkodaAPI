# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 0.0.x-alpha | Yes, during alpha development |

## Reporting a vulnerability

Please do **not** publish API keys, VINs, access tokens, vehicle locations, or other credentials in a public GitHub issue.

For security-sensitive reports, use GitHub's private vulnerability reporting mechanism when available:

https://github.com/janreimen/Domoticz-MySkodaAPI/security/advisories

Repository: https://www.github.com/janreimen/Domoticz-MySkodaAPI

## Credentials

The MyŠkoda API key is a vehicle credential.

Never commit it to Git or GitHub and never put it into screenshots, public logs, issue reports, or example configuration files.

The plugin accepts the API key through the Domoticz hardware configuration password field and sends it as the `X-API-Key` HTTP header. The plugin does not intentionally log the API key.

## Vehicle data

MyŠkoda API responses can contain sensitive vehicle information, including VIN, registration information and parking coordinates/address. Treat raw responses and Domoticz logs as private data.

Before opening an issue, redact at least:

- API keys
- VIN
- registration/plate number
- latitude/longitude
- parking address
- personal account information

## Remote commands

Version `0.0.1-alpha` is read-only. It does not implement remote vehicle commands.

This is intentional. Remote operations will only be considered after read-only vehicle capabilities and authorization behavior have been validated against the official API.

## Dependencies

Version `0.0.1-alpha` uses Python standard-library modules only and does not require third-party Python packages.
