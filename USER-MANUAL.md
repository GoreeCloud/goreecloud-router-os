# User Manual — GoreeCloud Router OS

## Current availability

GoreeCloud Router OS does **not** currently have a supported user-installable release. The repository is at Development / Milestone 0 and contains an unprivileged configuration-model and transaction-recovery prototype only.

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

The current merged Milestone 0 source includes tests for configuration invariants, deterministic planning, rollback, atomic transaction journaling, journal integrity, sensitive-field refusal, and interrupted-operation recovery. Passing these tests does not establish production router or virtual-machine network acceptance.

## Current recovery prototype

The source can optionally use a local atomic transaction journal while exercising the in-memory transaction model. Automatic recovery accepts only an exact previous or desired configuration revision. Corrupt journals or unknown third states are preserved and require explicit recovery instead of being overwritten automatically.

This journal is a development proof. It is not Everkeep integration, a production secret store, or evidence of real router filesystem, power-loss, kernel, daemon, or hardware recovery safety.

## What is not available yet

There is no supported firmware image, installer, web administration UI, authenticated management API, Wi-Fi management, production firewall/NAT backend, DHCP daemon integration, VPN service, remote administration, production update channel, or hardware support matrix.

Accepted Privacy Shield, Wardveil Security, Everkeep, GoreeCloud Mesh, GoreeCloud Identity, GoreeCloud Manager, and Glaze UI integration are also not established.

## Security and privacy

The prototype operates locally and includes no advertising telemetry, analytics SDK, remote logging service, packet capture, DNS-history collection, or production device discovery. Do not place passwords, private keys, production credentials, tokens, recovery codes, packet contents, or personally identifying network data in prototype configuration examples, tests, or local journal material.

Future Router OS security, privacy, recovery, networking, hardware, and platform-integration behavior must be documented as available only after it is implemented and verified. Until then, the current source remains a development proof and GoreeCloud Router OS remains Proposed.
