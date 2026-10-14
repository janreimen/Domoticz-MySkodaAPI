# Contributing to Domoticz-MySkodaAPI

Thank you for your interest in contributing to Domoticz-MySkodaAPI!

Contributions are welcome, including bug reports, vehicle compatibility testing, feature suggestions, documentation improvements, and code changes.

The purpose of this guide is to keep contributions safe, reproducible, and easy to review.

## 1. Before You Start

Before opening an issue or submitting a pull request:

1. Read the project's README and existing documentation.
2. Search existing issues and pull requests to avoid duplicates.
3. Check whether the problem is already fixed in the development branch.
4. Make sure you are using the correct plugin version and a supported Domoticz environment.

The plugin relies on Škoda's API. API behaviour, available data, and supported operations may change without notice.

## 2. Reporting Bugs

Please use the GitHub Bug Report template.

Include the following information whenever relevant:

- Plugin version.
- Domoticz version and operating system.
- Škoda model and model year.
- Whether the vehicle is fully electric, plug-in hybrid, or combustion-powered.
- Steps to reproduce the issue.
- Expected and actual behaviour.
- Relevant, redacted log output.

Please report whether the issue occurs consistently or intermittently.

Do not attach unredacted logs containing API keys, access tokens, passwords, complete VINs, precise GPS coordinates, or other personal data.

If the issue involves remote vehicle commands, describe the command and the observed result without exposing authentication secrets.

## 3. Suggesting Features

Use the GitHub Feature Request template.

Explain the problem you are trying to solve, the desired behaviour, and why the feature would be useful.

For vehicle-related features, identify the relevant vehicle models and whether the functionality is available through the API.

Suggestions involving remote vehicle control should describe the expected safety checks and user interaction.

## 4. Development Workflow

Contributions should normally target the `development` branch.

Do not submit changes directly to `master` unless the maintainer explicitly requests it.

### Fork and clone

Fork the repository on GitHub, then clone your fork:

```bash
git clone -b development https://github.com/YOUR_USERNAME/Domoticz-MySkodaAPI.git
cd Domoticz-MySkodaAPI
```

Add the upstream repository:

```bash
git remote add upstream https://github.com/janreimen/Domoticz-MySkodaAPI.git
git fetch upstream
```

Create a feature branch:

```bash
git switch -c feature/short-description
```

For a bug fix, a name such as `fix/device-update-error` is also suitable.

### Keep your branch up to date

```bash
git fetch upstream
git rebase upstream/development
```

Resolve any conflicts before continuing.

### Commit your changes

Use clear commit messages that describe the change:

```bash
git add .
git commit -m "Fix vehicle status update handling"
git push -u origin feature/short-description
```

Open a pull request against the upstream `development` branch.

Replace the example branch names and commit message with ones that describe your actual changes.

## 5. Coding Guidelines

- Follow the existing Python style and project structure.
- Keep changes focused on one issue or feature wherever practical.
- Avoid unrelated refactoring in bug-fix pull requests.
- Handle API errors, timeouts, and unexpected responses safely.
- Avoid unnecessary API requests and respect applicable API limits.
- Do not log authentication secrets or unnecessary personal vehicle data.
- Preserve existing Domoticz device identities and historical data when modifying device creation or update logic.
- Avoid introducing new dependencies unless they are justified and documented.
- Ensure that failures in one operation do not unnecessarily disrupt unrelated devices or plugin functionality.

### Vehicle commands and safety

Changes involving remote commands must account for API failures, rejected commands, timeouts, and uncertain command status.

Never report that a vehicle operation succeeded solely because a request was sent. Reflect the result only when supported by the available API response or subsequent vehicle state.

## 6. Testing

Before submitting a pull request:

- Check that modified Python files compile.
- Review the logs for new errors or unexpected behaviour.
- Test the affected functionality where possible.
- Verify that existing devices continue to update correctly.
- Check that configuration and error handling remain functional.
- Document any tests you could not perform.

For example:

```bash
python3 -m py_compile plugin.py
```

Run this command from the directory containing `plugin.py`.

Compilation is a basic syntax check, not a substitute for running the plugin in Domoticz.

If you cannot test against a real vehicle, state that clearly in your pull request.

## 7. Vehicle Compatibility Testing

Testing with additional Škoda models is particularly valuable.

When reporting compatibility, include the model, model year, powertrain type, plugin version, and the features tested.

Distinguish between:

- Confirmed working.
- Partially working.
- Not available for the tested vehicle.
- Not tested.

A missing value or unsupported command on one model does not necessarily indicate a general plugin defect.

## 8. Security and Privacy

Never commit or publish:

- API keys or access tokens.
- Passwords, cookies, or authentication headers.
- `.env` files containing secrets.
- Complete VINs or other identifying vehicle information.
- Precise GPS coordinates or sensitive journey information.
- Unredacted diagnostic logs containing personal information.

Use placeholders in examples, such as `YOUR_API_KEY` or `REDACTED_VIN`.

If you discover a security vulnerability, do not publish exploitable details or credentials in a public issue. Contact the maintainer privately.

## 9. Pull Request Requirements

Every pull request should:

- Target the `development` branch unless otherwise agreed.
- Explain the problem and the proposed solution.
- Reference the relevant issue, if one exists.
- Describe the tests performed and their results.
- Identify any limitations or untested behaviour.
- Include documentation updates when necessary.
- Avoid unrelated files, generated artifacts, and secrets.

The maintainer may request changes before merging.

## 10. Releases

Release and stable-branch changes are managed by the project maintainer.

Do not independently publish a release, change release tags, or merge into `master` without coordination.

Keep development changes focused and ensure that release-related version changes and documentation remain consistent when requested by the maintainer.

## 11. Questions and Support

For reproducible bugs and feature requests, use the repository's GitHub issue templates.

For general Domoticz usage questions, consult the Domoticz community resources and existing project documentation.

Thank you for helping improve Domoticz-MySkodaAPI!
