# Deployment Guide

## Domoticz MySkoda API Integration

This document describes how to install, configure, update, and remove the **MySkoda API Integration** plugin for Domoticz.

The plugin connects Domoticz to the MySkoda API and exposes vehicle information and controls as Domoticz devices.

---

## 1. Requirements

Before installing the plugin, make sure the following requirements are met:

* A working Domoticz installation
* Python 3
* Internet connectivity from the Domoticz host
* A valid MySkoda account
* A supported Škoda vehicle associated with the MySkoda account
* Permission to write to the Domoticz plugins directory

The plugin is designed for the Domoticz Python plugin architecture.

---

## 2. Installation

### 2.1 Locate the Domoticz plugins directory

The plugin must be installed inside the Domoticz `plugins` directory.

Typical locations include:

```text
/opt/domoticz/plugins
```

or, depending on the installation:

```text
/home/pi/domoticz/plugins
```

For a Docker-based Domoticz installation, use the directory that is mapped to the container's Domoticz plugins directory.

You can determine the active Domoticz installation directory from the Domoticz service/container configuration.

---

### 2.2 Clone the repository

Change to the Domoticz plugins directory:

```bash
cd /opt/domoticz/plugins
```

Clone the repository:

```bash
git clone https://github.com/janreimen/Domoticz-MySkodaAPI.git MySkodaAPI
```

The resulting directory should look similar to:

```text
plugins/
└── MySkodaAPI/
    ├── plugin.py
    ├── README.md
    ├── DEPLOY.md
    ├── SECURITY.md
    ├── LICENSE
    └── ...
```

---

## 3. Python Dependencies

The plugin uses Python 3.

Check the Python version:

```bash
python3 --version
```

The exact Python dependencies are defined by the project files shipped with the current release.

If the release contains a `requirements.txt`, install the dependencies with:

```bash
cd /opt/domoticz/plugins/MySkodaAPI
python3 -m pip install -r requirements.txt
```

If Domoticz uses a dedicated Python environment, install the dependencies into that environment instead of the system Python installation.

### Docker

For Docker deployments, dependencies must be installed inside the Domoticz container or included in the container image used by the deployment.

Do not install plugin dependencies only on the Docker host and expect them to be available inside the container.

---

## 4. File Permissions

The Domoticz process must be able to read the plugin files.

For example:

```bash
sudo chown -R domoticz:domoticz /opt/domoticz/plugins/MySkodaAPI
```

Adjust the user and group if Domoticz runs under a different account.

Verify:

```bash
ls -la /opt/domoticz/plugins/MySkodaAPI
```

The plugin files should be readable by the Domoticz process.

---

## 5. Configure the Plugin

Start or restart Domoticz after installing the plugin.

Open the Domoticz web interface and navigate to:

```text
Setup → Hardware
```

Select:

```text
MySkoda API Integration
```

Create a new hardware instance.

Enter the configuration values requested by the plugin.

### MySkoda credentials

Use the MySkoda account credentials associated with the vehicle.

**Do not put credentials directly into `plugin.py`.**

Credentials should only be entered through the Domoticz hardware configuration or the configuration mechanism documented by the current release.

Never commit credentials, authentication tokens, cookies, or other secrets to Git.

---

## 6. Vehicle Configuration

After the plugin successfully authenticates with MySkoda, it retrieves the vehicles associated with the account.

Select the vehicle that should be monitored by Domoticz.

For accounts containing multiple vehicles, make sure the correct vehicle is selected.

---

## 7. Restart Domoticz

After changing plugin configuration, restart Domoticz.

For a systemd installation:

```bash
sudo systemctl restart domoticz
```

Check the service:

```bash
sudo systemctl status domoticz
```

For Docker:

```bash
docker restart domoticz
```

Replace `domoticz` with the actual container name if necessary.

---

## 8. Verify the Installation

After restarting Domoticz:

1. Open the Domoticz web interface.
2. Go to **Setup → Hardware**.
3. Verify that **MySkoda API Integration** is present and enabled.
4. Open **Setup → Devices**.
5. Verify that the plugin-created devices are present.
6. Check the Domoticz log for plugin errors.

A successful installation should show the plugin starting without Python import or configuration errors.

---

## 9. Updating the Plugin

Before updating, check the release notes for the target version.

### Recommended Git update

Change to the plugin directory:

```bash
cd /opt/domoticz/plugins/MySkodaAPI
```

Check the current state:

```bash
git status
```

If the working tree is clean, fetch the latest version:

```bash
git fetch --tags
```

List available releases:

```bash
git tag
```

Check out the desired release:

```bash
git checkout <VERSION>
```

For example:

```bash
git checkout 0.0.1-alpha
```

Restart Domoticz:

```bash
sudo systemctl restart domoticz
```

### Important

Do not overwrite a working installation blindly with files from another release.

Always keep the deployed version identifiable so that the installation can be rolled back if necessary.

---

## 10. Updating From GitHub

To update to the latest repository state:

```bash
cd /opt/domoticz/plugins/MySkodaAPI
git fetch origin
git pull --ff-only
```

Then restart Domoticz:

```bash
sudo systemctl restart domoticz
```

Using `--ff-only` prevents Git from silently creating an unexpected merge commit on the deployment host.

---

## 11. Release Deployment

Production installations should preferably use a tagged release rather than an arbitrary development commit.

Example:

```bash
git fetch --tags
git checkout <VERSION>
```

Then verify:

```bash
git describe --tags --always
git status
```

The deployment should report the intended release/version.

### Release workflow

When preparing a new GitHub release, use the project's version progression consistently.

Do not skip an intermediate release when the repository workflow requires it.

For example, if development progresses through:

```text
0.0.1-alpha
        ↓
0.0.2-alpha
```

the intermediate release should be created and committed before moving the repository directly to the next target release.

---

## 12. Rollback

If a new release causes problems, return to the previously working release.

First inspect available tags:

```bash
cd /opt/domoticz/plugins/MySkodaAPI
git tag
```

Check out the previous version:

```bash
git checkout <PREVIOUS_VERSION>
```

Restart Domoticz:

```bash
sudo systemctl restart domoticz
```

Then verify the Domoticz log.

Example:

```bash
git checkout 0.0.1-alpha
sudo systemctl restart domoticz
```

---

## 13. Troubleshooting

### Plugin does not appear in Domoticz

Check that the directory is located directly below the Domoticz plugins directory:

```text
plugins/MySkodaAPI/plugin.py
```

Check the file:

```bash
ls -l /opt/domoticz/plugins/MySkodaAPI/plugin.py
```

Restart Domoticz after correcting the installation.

---

### Python error during startup

Check the Domoticz log.

Look for messages containing:

```text
MySkoda
Traceback
ImportError
ModuleNotFoundError
SyntaxError
```

Run a basic syntax check:

```bash
python3 -m py_compile /opt/domoticz/plugins/MySkodaAPI/plugin.py
```

A successful command produces no output.

---

### Dependency missing

A message such as:

```text
ModuleNotFoundError
```

usually indicates that a required Python dependency is missing.

Install the dependencies specified by the release:

```bash
cd /opt/domoticz/plugins/MySkodaAPI
python3 -m pip install -r requirements.txt
```

Restart Domoticz afterwards.

---

### Authentication failure

Verify:

* MySkoda username
* MySkoda password
* vehicle association with the account
* Internet connectivity
* plugin configuration
* current plugin version

Do not publish MySkoda credentials or authentication tokens in an issue, log, screenshot, or GitHub repository.

---

### API errors

MySkoda API behaviour can change independently of the Domoticz plugin.

If authentication succeeds but vehicle data cannot be retrieved:

1. Check the Domoticz log.
2. Record the HTTP status/error without exposing credentials or tokens.
3. Check the repository issues for known problems.
4. Verify that the installed version is current.
5. Upgrade only after reviewing the release notes.

---

## 14. Logging and Diagnostics

When diagnosing problems, collect the relevant Domoticz log entries.

Avoid posting:

* MySkoda username
* MySkoda password
* access tokens
* refresh tokens
* cookies
* authorization headers
* vehicle-identifying information that is not required for troubleshooting

Replace sensitive values with:

```text
<REDACTED>
```

before sharing logs.

---

## 15. Removing the Plugin

Before removing the plugin, disable the hardware instance in Domoticz.

Then stop or restart Domoticz as appropriate.

Remove the plugin directory:

```bash
sudo rm -rf /opt/domoticz/plugins/MySkodaAPI
```

Restart Domoticz:

```bash
sudo systemctl restart domoticz
```

Plugin-created Domoticz devices may need to be removed separately through the Domoticz web interface.

---

## 16. Docker Deployment

For a Docker-based Domoticz installation, the plugin must be available inside the Domoticz container.

A typical setup uses a persistent volume for the Domoticz data directory.

Example concept:

```text
Host
└── domoticz/
    └── plugins/
        └── MySkodaAPI/
```

mapped into the container's Domoticz data/plugins directory.

After installing or updating the plugin on the host-mounted directory:

```bash
docker restart domoticz
```

Verify the plugin from inside the container if required:

```bash
docker exec -it domoticz ls -la /opt/domoticz/plugins/MySkodaAPI
```

The exact container path depends on the Domoticz Docker image and volume configuration.

---

## 17. Production Deployment Checklist

Before considering a deployment complete:

* [ ] Domoticz is running correctly.
* [ ] Python 3 is available.
* [ ] Plugin files are in the correct `plugins` directory.
* [ ] Required Python dependencies are installed.
* [ ] File permissions allow Domoticz to read the plugin.
* [ ] The plugin appears under **Setup → Hardware**.
* [ ] MySkoda credentials are configured securely.
* [ ] The correct vehicle is selected.
* [ ] Domoticz has been restarted.
* [ ] MySkoda devices appear under **Setup → Devices**.
* [ ] No authentication errors are present.
* [ ] No Python exceptions are present in the Domoticz log.
* [ ] The deployed Git version/tag has been recorded.

---

## 18. Security

Security-related information and vulnerability reporting are documented separately in:

```text
SECURITY.md
```

Never commit credentials or authentication tokens to this repository.

If credentials have accidentally been committed, assume they are compromised and rotate/revoke them immediately.

---

## 19. Support

For problems with the plugin, provide:

* plugin version
* Domoticz version
* Python version
* operating system
* installation type (native/Docker)
* relevant Domoticz log entries

Remove all credentials and authentication information before submitting logs.

Project repository:

https://github.com/janreimen/Domoticz-MySkodaAPI

