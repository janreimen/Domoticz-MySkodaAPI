name: Bug report
description: Report a reproducible problem with Domoticz-MySkodaAPI
title: "[Bug]: "
labels:
  - bug
body:
  - type: markdown
    attributes:
      value: |
        Thank you for reporting a problem.

        Please search existing issues first. Never include API keys, access tokens, complete VINs, precise GPS coordinates, or unredacted personal data.

  - type: input
    id: plugin_version
    attributes:
      label: Plugin version
      description: The exact version shown by your installation.
      placeholder: "e.g. 0.4.4.002"
    validations:
      required: true

  - type: input
    id: domoticz_version
    attributes:
      label: Domoticz version
      description: Include the build or release identifier if available.
      placeholder: "e.g. 2026.4"
    validations:
      required: true

  - type: input
    id: operating_system
    attributes:
      label: Operating system
      description: Include the platform and version.
      placeholder: "e.g. Raspberry Pi OS, Debian, Synology DSM"
    validations:
      required: true

  - type: dropdown
    id: vehicle_model
    attributes:
      label: Škoda model
      description: Select the closest match.
      options:
        - Octavia
        - Superb
        - Fabia
        - Scala
        - Kamiq
        - Karoq
        - Kodiaq
        - Enyaq
        - Elroq
        - Other
        - Multiple vehicles
    validations:
      required: true

  - type: input
    id: model_year
    attributes:
      label: Vehicle model year
      placeholder: "e.g. 2026"
    validations:
      required: false

  - type: dropdown
    id: powertrain
    attributes:
      label: Powertrain
      options:
        - Battery electric (BEV)
        - Plug-in hybrid (PHEV)
        - Petrol
        - Diesel
        - Other / unknown
    validations:
      required: true

  - type: dropdown
    id: issue_area
    attributes:
      label: Affected functionality
      options:
        - Installation or configuration
        - Authentication or API connection
        - Vehicle data or status updates
        - Domoticz device creation or deletion
        - Battery, charging, or range
        - Mileage or driving data
        - Climate or remote commands
        - Plugin startup or shutdown
        - Other
    validations:
      required: true

  - type: textarea
    id: problem
    attributes:
      label: Describe the problem
      description: Explain what happens and why it is unexpected.
      placeholder: A clear description of the problem.
    validations:
      required: true

  - type: textarea
    id: reproduce
    attributes:
      label: Steps to reproduce
      description: List the actions needed to reproduce the issue.
      placeholder: |
        1. Configure the plugin...
        2. Wait for an update...
        3. Observe the result...
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: Expected behaviour
      placeholder: What should happen?
    validations:
      required: true

  - type: textarea
    id: logs
    attributes:
      label: Relevant logs
      description: Include only relevant, redacted log excerpts. Remove credentials, tokens, VINs, GPS coordinates, and personal information.
      render: text
    validations:
      required: false

  - type: textarea
    id: additional
    attributes:
      label: Additional information
      description: Mention whether the issue is reproducible and whether it worked in an earlier version.
    validations:
      required: false

  - type: checkboxes
    id: checklist
    attributes:
      label: Before submitting
      options:
        - label: I searched existing issues for a similar problem.
          required: true
        - label: I removed credentials and personal vehicle data from this report.
          required: true
