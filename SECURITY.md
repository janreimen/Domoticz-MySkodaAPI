# Security Policy

## Domoticz MySkoda API Integration

The **Domoticz MySkoda API Integration** project takes security and responsible handling of credentials seriously.

This document describes how to report security vulnerabilities and how sensitive information should be handled when using or contributing to the project.

---

## Supported Versions

Security fixes are generally applied to actively maintained releases.

| Version                            | Supported      |
| ---------------------------------- | -------------- |
| Latest stable release              | ✅ Yes          |
| Previous stable release            | ⚠️ Best effort |
| Development / pre-release versions | ⚠️ Best effort |
| End-of-life releases               | ❌ No           |

Users should run the latest available release whenever possible.

---

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability, please report it privately to the project maintainer.

Include:

* A description of the vulnerability
* The affected version
* Steps required to reproduce the issue
* Potential security impact
* Any relevant logs or proof-of-concept information

Do **not** include real passwords, authentication tokens, session cookies, or other credentials in the report.

If sensitive information is required to reproduce the issue, redact it before submitting the report.

---

## What Should Be Reported Privately?

Examples of security issues include:

* Exposure of MySkoda credentials
* Exposure of authentication or refresh tokens
* Credentials being written to logs
* Improper handling of API authentication data
* Unauthorized access to vehicle information
* Authentication bypasses
* Insecure storage of credentials
* Remote code execution
* Command injection
* Path traversal
* Unexpected disclosure of personally identifiable information
* Vulnerabilities introduced by third-party dependencies

If you are unsure whether an issue is security-related, report it privately rather than publishing the details.

---

## Credentials and Secrets

Never commit secrets to the Git repository.

This includes:

```text
MySkoda username
MySkoda password
Access tokens
Refresh tokens
Session cookies
API keys
Authorization headers
Private keys
```

Do not place real credentials in:

```text
plugin.py
README.md
DEPLOY.md
SECURITY.md
.env.example
GitHub Issues
GitHub Discussions
Pull Requests
Public logs
Screenshots
```

Use placeholders instead:

```text
<USERNAME>
<PASSWORD>
<ACCESS_TOKEN>
<REDACTED>
```

---

## Configuration Security

The MySkoda account credentials used by the plugin should be protected in the same way as any other account credentials.

Recommended practices:

* Use a strong, unique MySkoda password.
* Do not share your Domoticz configuration with credentials included.
* Restrict access to the Domoticz web interface.
* Use HTTPS when exposing Domoticz remotely.
* Keep Domoticz and the operating system updated.
* Keep the plugin updated.
* Restrict access to the host running Domoticz.
* Avoid exposing the Domoticz API directly to the Internet.

---

## Logging

Logs can contain information useful for troubleshooting but may also reveal sensitive information.

Before sharing logs publicly, inspect them for:

* usernames
* email addresses
* authentication tokens
* cookies
* authorization headers
* vehicle identifiers
* VINs
* location information
* personally identifiable information

Redact sensitive values before publishing logs.

For example:

```text
Authorization: Bearer <REDACTED>
```

instead of:

```text
Authorization: Bearer eyJ...
```

---

## Vehicle and Personal Data

The plugin may process vehicle-related information obtained through the MySkoda API.

Depending on the vehicle and API functionality, this may include information such as:

* vehicle status
* battery/charging information
* vehicle location
* mileage
* service information
* vehicle identifiers

Treat this information as potentially sensitive.

Do not publish vehicle data unnecessarily in GitHub issues, screenshots, logs, or documentation.

---

## Git Repository Security

Contributors must ensure that secrets are not committed to Git.

Before creating a commit, review:

```bash
git status
git diff
```

Before pushing changes, review the files that will be committed:

```bash
git diff --cached
```

Never commit:

```text
.env
credentials files
private keys
tokens
password databases
personal configuration files
```

The repository may provide `.env.example` or similar example configuration files. These must contain placeholders only.

---

## If a Secret Is Accidentally Committed

Removing a secret from the latest commit is **not sufficient** if the commit has already been pushed.

Assume the secret is compromised.

Immediately:

1. Revoke or rotate the affected credential.
2. Remove the secret from the working tree.
3. Notify the project maintainer if appropriate.
4. Remove the secret from Git history where necessary.
5. Check whether the exposed credential was accessed or abused.

For authentication credentials, **rotation/revocation is more important than simply deleting the file from the repository**.

---

## Dependencies

The project may depend on third-party Python packages and external services.

Users should:

* Keep dependencies up to date.
* Review security advisories affecting dependencies.
* Avoid installing packages from untrusted sources.
* Use the dependency versions specified by the project where applicable.

Security issues in a third-party dependency should be evaluated according to the impact they have on this project.

---

## API Security

The plugin communicates with external MySkoda services.

API availability, authentication mechanisms, endpoints, and server-side security are controlled by the service provider and may change independently of this project.

The plugin does not control the security of the MySkoda infrastructure.

If an issue appears to originate from the upstream service rather than this plugin, it may need to be reported to the relevant service provider as well.

---

## Domoticz Security

The plugin runs within the Domoticz environment.

A compromised Domoticz installation may therefore compromise the plugin and its configuration.

Users should secure the underlying Domoticz installation by:

* Restricting network access
* Using strong authentication
* Using HTTPS where appropriate
* Keeping Domoticz updated
* Keeping the operating system updated
* Running services with appropriate privileges
* Avoiding unnecessary Internet exposure
* Using firewall rules where appropriate

The plugin should not be considered a security boundary.

---

## Responsible Disclosure

Security researchers are encouraged to provide sufficient information to reproduce and understand a vulnerability while avoiding unnecessary disclosure of sensitive information.

Please allow reasonable time for investigation and remediation before publicly disclosing a vulnerability.

The project maintainer may coordinate disclosure and release information depending on the severity and impact of the vulnerability.

---

## Security Updates

Security fixes may be released as:

* Patch releases
* Updated dependencies
* Configuration changes
* Documentation updates
* Emergency releases where required

Users should monitor the project repository for security-related releases and upgrade promptly when a vulnerability affects their installation.

---

## Contact

For security-related reports, use the private contact mechanism provided by the project maintainer or GitHub repository.

**Do not use public GitHub Issues for undisclosed security vulnerabilities.**

For general bugs and feature requests, use the project's normal GitHub issue tracker instead.

---

## Disclaimer

This project is provided on an "as is" basis.

The plugin communicates with external services and depends on Domoticz, Python, third-party libraries, network infrastructure, and the MySkoda service.

Users are responsible for securing their Domoticz installation, operating system, network, and MySkoda account.

