# User Manual — GoreeCloud Router OS

## Current availability

GoreeCloud Router OS does **not** currently have a supported user-installable release. The repository is at Development / Milestone 0 and contains a configuration-model and transaction-recovery architecture core plus isolated Development-only namespace test/execution infrastructure.

## Intended audience for the current repository

The current runnable material is for authorized GoreeCloud development and validation. It does not provide a supported router installation and must not be used as production network software.

## Running the prototype validator

Requirements: Python 3.11 or newer.

From the repository root:

```bash
python scripts/validate_config.py config/examples/reference-build-0.1.json
```

A successful validation reports the normalized revision digest and a preview of the abstract plan. The validator does not execute system networking commands.

Run the unit tests with:

```bash
python -m unittest discover -s tests -v
```

The current Milestone 0 source includes tests for configuration invariants, deterministic planning, preview/review consistency, rollback, atomic transaction journaling, journal integrity, interrupted recovery, virtual-lab plan safety, and the bounded privileged adapter.

## Current recovery prototype

The source can optionally use a local atomic transaction journal while exercising the in-memory transaction model. Automatic recovery accepts only an exact previous or desired configuration revision. Corrupt journals or unknown third states are preserved and require explicit recovery instead of being overwritten automatically.

This journal is a development proof. It is not Everkeep integration, a production secret store, or evidence of real router filesystem, power-loss, kernel, daemon, or hardware recovery safety.

## Privileged Development test boundary

The repository includes Linux network-namespace tests that require root privileges. One harness validates isolated routed topology. A second Development-only adapter can configure only an allowlisted static LAN interface and IPv4 forwarding inside a dedicated `gcr-a-<digits>` namespace.

These privileged paths are intended for isolated CI acceptance, not ordinary end-user use. They do not provide a host-network executor, complete Reference Build runtime, firmware installation path, nftables/NAT backend, DHCP service, management API, or production privilege model. The complete Reference Build plan is intentionally refused while those backends are missing.

## What is not available yet

There is no supported firmware image, installer, web administration UI, authenticated management API, Wi-Fi management, production firewall/NAT backend, DHCP daemon integration, VPN service, remote administration, production update channel, or hardware support matrix.

Accepted Privacy Shield, Wardveil Security, Everkeep, GoreeCloud Mesh, GoreeCloud Identity, GoreeCloud Manager, and Glaze UI integration are also not established.

## Security and privacy

The development source includes no advertising telemetry, analytics SDK, remote logging service, packet capture, DNS-history collection, or production device discovery. Do not place passwords, private keys, production credentials, tokens, recovery codes, packet contents, or personally identifying network data in prototype configuration examples, tests, journal material, or CI fixtures.

Future Router OS security, privacy, recovery, networking, hardware, and platform-integration behavior must be documented as available only after it is implemented and verified. Until then, the source remains Development and GoreeCloud Router OS remains Proposed.
