# GoreeCloud Router OS

GoreeCloud Router OS is a proposed first-party router, firewall, network-edge, and local-network management platform for GoreeCloud.

## Current state

This repository is in **Development / Milestone 0**. It does not contain a supported Router OS release, production firmware, or a production-ready network-control plane. The current executable material is a safe proof-of-architecture for the canonical configuration model, deterministic planning, validation, verification, rollback, atomic transaction journaling, and interrupted-operation reconciliation. It intentionally does **not** modify host interfaces, firewall rules, routes, DHCP services, DNS, VPNs, or other privileged networking state.

The canonical product specification is maintained in GoreeCloud Google Drive as `GoreeCloud/Projects/Project Specification — Router OS.docx`. Repository-local specifications are version-coupled development records and must not override authoritative GoreeCloud governance.

## Milestone 0 prototype

The prototype models the narrow Reference Build 0.1 target defined by the canonical specification: one DHCP WAN, one static LAN, IPv4 forwarding intent, LAN DHCP intent, stateful-firewall intent, and safe apply/verify/rollback behavior. It emits an abstract execution plan only.

An optional `AtomicJournalStore` now records transaction phase transitions using a local JSON journal written with temp-file flush/fsync and atomic replace semantics. The current journal accepts only the secret-free Milestone 0 configuration shape, rejects defined sensitive field names, uses a restrictive file mode on POSIX, and is removed after a verified terminal state. `recover_interrupted_transaction` automatically accepts only an exact previous or desired configuration revision; corrupt journals or third runtime states remain untouched and require explicit recovery.

This journal is a development proof, not Everkeep, not a production secret store, and not evidence of crash/power-loss safety on a real router filesystem.

Run the checks locally with:

```bash
python -m unittest discover -s tests -v
python scripts/validate_config.py config/examples/reference-build-0.1.json
```

## Repository map

- `prototype/routeros_m0/` — unprivileged Milestone 0 configuration/transaction/recovery proof.
- `config/` — versioned schema and sanitized examples.
- `tests/` — unit tests for invariants, rollback, journal integrity, and interrupted recovery semantics.
- `docs/architecture/` — repository-local engineering detail.
- `.github/workflows/` — automated validation for the current prototype.

## Governance and status

The project follows GoreeCloud repository governance. Platform-system integrations including GoreeCloud Manager, Privacy Shield, Wardveil Security, Everkeep, Glaze UI, GoreeCloud Mesh, and GoreeCloud Identity remain blocked/unaccepted unless verified by separate evidence. GoreeCloud Network/Conduit and GoreeCloud Beacon remain separate authorities for private networking and DNS respectively.

See `SPECIFICATIONS.md`, `FEATURES.md`, `FEATURE-ROADMAP.md`, `SECURITY.md`, `PRIVACY POLICY.md`, and `USER-MANUAL.md` for the current development boundary.
