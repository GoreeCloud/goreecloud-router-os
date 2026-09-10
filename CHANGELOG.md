# Changelog

This repository changelog records source-level development milestones. The canonical GoreeCloud project changelog is maintained separately in Google Drive.

## Unreleased — Milestone 0

- Established the governed repository baseline.
- Added the unprivileged Reference Build 0.1 configuration/state proof-of-architecture.
- Added deterministic validation, compilation, transaction, verification, and rollback tests.
- Added truthful Platform Contract state with blocked/unaccepted integrations.
- Added an optional atomic, integrity-checked local transaction journal for prepared/applied/retained/rolled-back phase evidence.
- Added sensitive-field refusal for journal persistence and restrictive POSIX journal permissions.
- Added fail-closed interrupted-transaction recovery that accepts only exact desired/previous revisions and preserves corrupt or third-state evidence.
- Expanded automated Milestone 0 tests to cover journal persistence, integrity failure, privacy refusal, and interrupted recovery behavior.
