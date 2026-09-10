# GoreeCloud Router OS

GoreeCloud Router OS is a proposed first-party router, firewall, network-edge, and local-network management platform for GoreeCloud.

## Current state

This repository is in **Development / Milestone 0**. It does not contain a supported Router OS release, production firmware, or a production-ready network-control plane. The current executable material is a safe proof-of-architecture for the canonical configuration model, deterministic planning, validation, verification, and rollback semantics. It intentionally does **not** modify host interfaces, firewall rules, routes, DHCP services, DNS, VPNs, or other privileged networking state.

The canonical product specification is maintained in GoreeCloud Google Drive as `GoreeCloud/Projects/Project Specification — Router OS.docx`. Repository-local specifications are version-coupled development records and must not override authoritative GoreeCloud governance.

## Milestone 0 prototype

The prototype models the narrow Reference Build 0.1 target defined by the canonical specification: one DHCP WAN, one static LAN, IPv4 forwarding intent, LAN DHCP intent, stateful-firewall intent, and safe apply/verify/rollback behavior. It emits an abstract execution plan only.

Run the checks locally with:

```bash
python -m unittest discover -s tests -v
python scripts/validate_config.py config/examples/reference-build-0.1.json
```

## Repository map

- `prototype/routeros_m0/` — unprivileged Milestone 0 configuration/transaction proof.
- `config/` — versioned schema and sanitized examples.
- `tests/` — unit tests for invariants and rollback semantics.
- `docs/architecture/` — repository-local engineering detail.
- `.github/workflows/` — automated validation for the current prototype.

## Governance and status

The project follows GoreeCloud repository governance. Platform-system integrations including GoreeCloud Manager, Privacy Shield, Wardveil Security, Everkeep, Glaze UI, GoreeCloud Mesh, and GoreeCloud Identity remain blocked/unaccepted unless verified by separate evidence. GoreeCloud Network/Conduit and GoreeCloud Beacon remain separate authorities for private networking and DNS respectively.

See `SPECIFICATIONS.md`, `FEATURES.md`, `FEATURE-ROADMAP.md`, `SECURITY.md`, `PRIVACY POLICY.md`, and `USER-MANUAL.md` for the current development boundary.
