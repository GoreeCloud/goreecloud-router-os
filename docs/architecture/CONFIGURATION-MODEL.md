# Milestone 0 Configuration Model

## Purpose

This document describes the repository's current proof-of-architecture for Router OS configuration state. It is subordinate to the canonical GoreeCloud Router OS product specification.

## State separation

The prototype models four distinct concepts:

1. **Candidate** — operator-supplied configuration before acceptance.
2. **Desired** — normalized, validated configuration with a deterministic revision digest.
3. **Applied** — state the adapter reports after an apply operation.
4. **Observed** — separately read state used to verify that the runtime matches the desired revision.

A candidate is never treated as applied merely because parsing succeeded. A successful apply is not retained until observed state matches the desired revision.

## Deterministic revision identity

The prototype serializes normalized configuration with stable key ordering and computes a SHA-256 digest. The digest is development evidence for exact configuration identity; it is not a security attestation or production signature.

## Compilation boundary

`compiler.py` converts validated desired state into an abstract list of structured operations. The prototype has no executor for these operations. A future privileged adapter must map approved operation types to Linux networking APIs/commands through a narrow, auditable boundary.

## Transaction boundary

`transaction.py` snapshots the prior known-good state, applies the desired state to an in-memory runtime, observes the result, and retains only when observed and desired revision identities match. Verification mismatch restores the previous snapshot.

When an `AtomicJournalStore` is supplied, the transaction records a prepared phase before apply, an applied phase after the runtime reports apply completion, and a terminal retained/rolled-back phase before cleanup. Normal terminal transactions clear the journal after the runtime state is confirmed.

## Atomic journal proof

`journal.py` implements a deliberately narrow development journal for the current secret-free Reference Build 0.1 configuration. It:

- normalizes desired and previous configurations and records their revision digests;
- refuses defined sensitive field names rather than silently persisting them;
- serializes one versioned JSON envelope with a SHA-256 consistency checksum;
- writes through a temporary file, flushes and fsyncs it, atomically replaces the target, and fsyncs the parent directory where supported;
- applies a `0600` file mode on POSIX systems;
- rejects unknown journal fields, invalid phases, digest mismatches, malformed JSON, and checksum mismatches.

The checksum is not keyed and therefore is not a substitute for authenticated storage or adversarial tamper protection.

## Interrupted-operation recovery

`recovery.py` reads the journal and compares observed runtime state with the exact previous and desired revision identities. Automatic reconciliation is intentionally limited:

- **Prepared + previous observed**: discard the unapplied journal.
- **Prepared + desired observed**: finalize the desired state as retained.
- **Applied + desired observed**: finalize the desired state as retained.
- **Applied + previous observed**: confirm rollback.
- **Terminal phase + matching runtime**: clear the stale terminal journal.
- **Corrupt journal or third runtime state**: preserve evidence and raise `RecoveryRequired` instead of overwriting an unknown state.

This fail-closed behavior is a proof of recovery decision semantics. It does not yet restore real Linux networking state, survive verified power-loss fault injection, or integrate with Everkeep.

## Current limitation

The prototype still uses only an in-memory runtime adapter. It does not prove daemon restart behavior, kernel networking atomicity, hardware behavior, production filesystem crash consistency, or power-loss recovery. Those remain required acceptance work before a privileged backend or Reference Build 0.1 can be treated as production-capable.
