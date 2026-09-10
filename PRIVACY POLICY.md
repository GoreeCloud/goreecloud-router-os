# GoreeCloud Router OS — Privacy Policy

## Scope of this repository state

GoreeCloud Router OS is currently a Development / Milestone 0 prototype and is not an operating production router service.

The current prototype:

- processes operator-supplied JSON configuration locally;
- computes deterministic configuration digests locally;
- produces an in-memory abstract execution plan;
- uses an in-memory mock runtime for transaction tests;
- contains no advertising telemetry, analytics SDK, remote logging service, or cloud account flow.

The current prototype does not capture packets, inspect traffic, collect DNS history, enumerate real network devices, or transmit configuration data to GoreeCloud services.

## Sensitive data

Do not place production credentials, authentication tokens, private keys, recovery codes, packet contents, or personally identifying network data in repository examples or tests.

## Future behavior

The canonical product specification requires Privacy Shield governance, minimal collection by default, local-first processing where practical, configurable retention, privacy-safe diagnostics, and sensitive-value redaction. Those future requirements are not represented here as implemented or accepted.

This file must be updated when actual runtime data handling changes.
