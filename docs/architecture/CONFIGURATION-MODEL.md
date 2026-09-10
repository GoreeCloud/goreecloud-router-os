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

This proves the control-flow contract only. It does not prove filesystem crash consistency, daemon restart behavior, kernel networking atomicity, hardware behavior, or power-loss recovery.
