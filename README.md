# GoreeCloud Router OS

GoreeCloud Router OS is a proposed first-party router, firewall, network-edge, and local-network management platform for GoreeCloud.

## Current state

This repository is in **Development / Milestone 0**. It does not contain a supported Router OS release, production firmware, or a production-ready network-control plane. The product prototype currently proves canonical configuration identity, validation, deterministic abstract planning, privacy-safe change preview, review/apply consistency, in-memory verification/rollback, atomic transaction journaling, and interrupted-operation reconciliation. The product prototype itself does **not** modify host interfaces, firewall rules, routes, DHCP services, DNS, VPNs, or other privileged networking state.

The repository also contains a separate **development-only virtual network lab**. That harness uses temporary Linux network namespaces and veth pairs on an ephemeral CI runner to prove isolated routed topology and teardown behavior. Lab privileges are not Router OS runtime privileges and do not establish a production execution adapter.

The canonical product specification is maintained in GoreeCloud Google Drive as `GoreeCloud/Projects/Project Specification — Router OS.docx`. Repository-local specifications are version-coupled development records and must not override authoritative GoreeCloud governance.

## Milestone 0 prototype

The prototype models the narrow Reference Build 0.1 target defined by the canonical specification: one DHCP WAN, one static LAN, IPv4 forwarding intent, LAN DHCP intent, stateful-firewall intent, and safe preview/apply/verify/rollback behavior. It still emits only an abstract product execution plan.

An optional `AtomicJournalStore` records transaction phase transitions using a local JSON journal written with temp-file flush/fsync and atomic replace semantics. The current journal accepts only the secret-free Milestone 0 configuration shape, rejects defined sensitive field names, uses a restrictive file mode on POSIX, and is removed after a verified terminal state. `recover_interrupted_transaction` automatically accepts only an exact previous or desired configuration revision; corrupt journals or third runtime states remain untouched and require explicit recovery.

The virtual lab creates an upstream namespace, router namespace, and LAN-client namespace, verifies routed connectivity through the router namespace, confirms that the host default route is unchanged, and verifies that all generated namespaces are removed. It does not yet run a Router OS nftables backend, NAT backend, DHCP server, or authenticated management API.

The journal is a development proof, not Everkeep, not a production secret store, and not evidence of crash/power-loss safety on a real router filesystem. The namespace lab is development test infrastructure, not production networking acceptance.

Run the unprivileged checks locally with:

```bash
python -m unittest discover -s tests -v
python scripts/validate_config.py config/examples/reference-build-0.1.json --check-only
python lab/reference_build_0_1.py --plan
```

The full namespace smoke test requires Linux network-namespace capability and root privileges and is run by GitHub Actions on the isolated hosted runner.

## Repository map

- `prototype/routeros_m0/` — unprivileged Milestone 0 configuration/transaction/recovery proof.
- `lab/` — development-only isolated Reference Build 0.1 network laboratory.
- `config/` — versioned schema and sanitized examples.
- `tests/` — unit tests for invariants, preview/review consistency, rollback, journal integrity, recovery, and lab-plan safety.
- `docs/architecture/` — repository-local engineering detail.
- `.github/workflows/` — automated validation for the current prototype and lab harness.

## Governance and status

The project follows GoreeCloud repository governance. Platform-system integrations including GoreeCloud Manager, Privacy Shield, Wardveil Security, Everkeep, Glaze UI, GoreeCloud Mesh, and GoreeCloud Identity remain blocked/unaccepted unless verified by separate evidence. GoreeCloud Network/Conduit and GoreeCloud Beacon remain separate authorities for private networking and DNS respectively.

See `SPECIFICATIONS.md`, `FEATURES.md`, `FEATURE-ROADMAP.md`, `SECURITY.md`, `PRIVACY POLICY.md`, and `USER-MANUAL.md` for the current development boundary.
