# GoreeCloud Router OS — Privacy Policy

## Scope of this repository state

GoreeCloud Router OS is currently a Development / Milestone 0 prototype and is not an operating production router service.

The current prototype:

- processes operator-supplied JSON configuration locally;
- computes deterministic configuration digests locally;
- produces an in-memory abstract execution plan;
- uses an in-memory mock runtime for transaction tests;
- can optionally persist a local transaction journal containing the current secret-free desired and previous prototype configurations while an apply/recovery decision is in progress;
- removes a normal terminal journal after the retained or rolled-back runtime state is confirmed;
- can preserve a journal when corruption or an unknown third runtime state requires explicit recovery;
- contains no advertising telemetry, analytics SDK, remote logging service, or cloud account flow.

The current journal explicitly refuses defined sensitive field names such as passwords, tokens, secrets, private keys, credentials, API keys, and recovery codes. This is a narrow development safeguard, not a complete production data-classification system.

The current prototype does not capture packets, inspect traffic, collect DNS history, enumerate real network devices, or transmit configuration data to GoreeCloud services.

## Sensitive data

Do not place production credentials, authentication tokens, private keys, recovery codes, packet contents, or personally identifying network data in repository examples, tests, or the Milestone 0 journal.

## Future behavior

The canonical product specification requires Privacy Shield governance, minimal collection by default, local-first processing where practical, configurable retention, privacy-safe diagnostics, and sensitive-value redaction. Those future requirements are not represented here as implemented or accepted.

This file must be updated when actual runtime data handling changes.
