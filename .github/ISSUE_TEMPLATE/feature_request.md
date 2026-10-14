name: Feature request
description: Suggest an improvement or new capability
title: "[Feature]: "
labels:
  - enhancement
body:
  - type: markdown
    attributes:
      value: |
        Describe the problem you want to solve and the proposed improvement.

        For vehicle-specific functionality, explain which models or API capabilities are relevant. Do not include credentials or personal vehicle data.

  - type: textarea
    id: problem
    attributes:
      label: Is your feature request related to a problem?
      description: Explain the limitation or use case.
      placeholder: I would like to be able to...
    validations:
      required: true

  - type: textarea
    id: solution
    attributes:
      label: Proposed solution
      description: Describe how you would like the feature to work.
      placeholder: The plugin should...
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives considered
      description: Describe any workarounds or alternative solutions.
    validations:
      required: false

  - type: dropdown
    id: category
    attributes:
      label: Feature category
      options:
        - Vehicle telemetry or status
        - Battery, charging, or range
        - Mileage or driving data
        - Climate or remote commands
        - Domoticz devices or presentation
        - Configuration or installation
        - Logging or diagnostics
        - Other
    validations:
      required: true

  - type: input
    id: vehicle
    attributes:
      label: Relevant Škoda model(s)
      description: Enter the model and model year if relevant.
      placeholder: "e.g. Enyaq 2025, Octavia 2026"
    validations:
      required: false

  - type: textarea
    id: api
    attributes:
      label: API availability or limitations
      description: If known, explain whether the functionality is available through the Škoda API.
    validations:
      required: false

  - type: textarea
    id: additional
    attributes:
      label: Additional context
      description: Screenshots or examples are welcome if all sensitive information is removed.
    validations:
      required: false

  - type: checkboxes
    id: checklist
    attributes:
      label: Before submitting
      options:
        - label: I checked existing issues and documentation for this feature.
          required: true
        - label: I have not included credentials or personal vehicle data.
          required: true
