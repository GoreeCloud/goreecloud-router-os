# User Manual — GoreeCloud Router OS

## Current availability

GoreeCloud Router OS does **not** currently have a supported user-installable release. The repository is at Development / Milestone 0 and contains an unprivileged configuration-model prototype only.

## Intended audience for the current repository

The current runnable material is for authorized GoreeCloud development and validation. It does not configure a real router and must not be used as production network software.

## Running the prototype validator

Requirements: Python 3.11 or newer.

From the repository root:

```bash
python scripts/validate_config.py config/examples/reference-build-0.1.json
```

A successful validation reports the normalized revision digest and a preview of the abstract plan. The preview does not execute system networking commands.

Run the unit tests with:

```bash
python -m unittest discover -s tests -v
```

## What is not available yet

There is no supported firmware image, installer, web administration UI, authenticated management API, Wi-Fi management, production firewall/NAT backend, DHCP daemon integration, VPN service, remote administration, production update channel, or hardware support matrix.

## Security and privacy

The prototype accepts only local configuration files supplied by the operator and does not include telemetry or a cloud service. Do not put passwords, private keys, production credentials, tokens, or sensitive packet data in prototype configuration examples or test fixtures.

Future Router OS security, privacy, recovery, and platform-integration behavior must be documented here only after it is implemented and verified.
