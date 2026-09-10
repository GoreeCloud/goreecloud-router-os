# GoreeCloud Router OS

GoreeCloud Router OS is a proposed first-party router, firewall, network-edge, and local-network management platform for GoreeCloud.

## Current state

This repository is in **Development / Milestone 0**. It does not contain a supported Router OS release, production firmware, or a production-ready network-control plane. The configuration/transaction core currently proves canonical configuration identity, validation, deterministic abstract planning, privacy-safe change preview, review/apply consistency, in-memory verification/rollback, atomic transaction journaling, and interrupted-operation reconciliation.

The repository also contains two separate Development-only privileged test components: the isolated virtual network lab and a bounded Linux namespace execution adapter. The adapter is restricted to dedicated `gcr-a-<digits>` namespaces and an explicit interface allowlist. It currently applies only static IPv4 LAN address/link state and router-namespace IPv4 forwarding. It does **not** provide host-network execution, WAN DHCP, nftables/NAT, LAN DHCP service control, or management API execution.

The complete Reference Build 0.1 compiled plan is intentionally refused before mutation because several required privileged backends remain unavailable. The configuration transaction path still uses `InMemoryRuntime`; the namespace adapter has not been promoted into product transactional apply/rollback.

The canonical product specification is maintained in GoreeCloud Google Drive as `GoreeCloud/Projects/Project Specification — Router OS.docx`. Repository-local specifications are version-coupled development records and must not override authoritative GoreeCloud governance.

## Milestone 0 prototype

The prototype models the narrow Reference Build 0.1 target defined by the canonical specification: one DHCP WAN, one static LAN, IPv4 forwarding intent, LAN DHCP intent, stateful-firewall intent, and safe preview/apply/verify/rollback behavior. The compiler emits a structured abstract product execution plan.

An optional `AtomicJournalStore` records transaction phase transitions using a local JSON journal written with temp-file flush/fsync and atomic replace semantics. The current journal accepts only the secret-free Milestone 0 configuration shape, rejects defined sensitive field names, uses a restrictive file mode on POSIX, and is removed after a verified terminal state. `recover_interrupted_transaction` automatically accepts only an exact previous or desired configuration revision; corrupt journals or third runtime states remain untouched and require explicit recovery.

The virtual lab creates an upstream namespace, router namespace, and LAN-client namespace, verifies routed connectivity through the router namespace, confirms that the host default route is unchanged, and verifies that all generated namespaces are removed. The separate privileged-adapter smoke test creates a disposable adapter namespace and proves only the current static-LAN and IPv4-forwarding operations plus teardown and host-route invariance.

The journal is a development proof, not Everkeep, not a production secret store, and not evidence of crash/power-loss safety on a real router filesystem. Namespace privileges are Development test privileges, not production Router OS privilege acceptance.

Run the unprivileged checks locally with:

```bash
python -m unittest discover -s tests -v
python scripts/validate_config.py config/examples/reference-build-0.1.json --check-only
python lab/reference_build_0_1.py --plan
```

The full namespace and privileged-adapter smoke tests require Linux network-namespace capability and root privileges and are run by GitHub Actions on an isolated hosted runner.

## Repository map

- `prototype/routeros_m0/` — Milestone 0 configuration/transaction/recovery proof plus the bounded namespace adapter.
- `lab/` — Development-only isolated Reference Build 0.1 network and adapter acceptance harnesses.
- `config/` — versioned schema and sanitized examples.
- `tests/` — unit tests for invariants, preview/review consistency, rollback, journal integrity, recovery, lab-plan safety, and privileged-adapter safety.
- `docs/architecture/` — repository-local engineering detail.
- `.github/workflows/` — automated validation for the current prototype and isolated privileged test harnesses.

## Governance and status

The project follows GoreeCloud repository governance. Platform-system integrations including GoreeCloud Manager, Privacy Shield, Wardveil Security, Everkeep, Glaze UI, GoreeCloud Mesh, and GoreeCloud Identity remain blocked/unaccepted unless verified by separate evidence. GoreeCloud Network/Conduit and GoreeCloud Beacon remain separate authorities for private networking and DNS respectively.

See `SPECIFICATIONS.md`, `FEATURES.md`, `FEATURE-ROADMAP.md`, `SECURITY.md`, `PRIVACY POLICY.md`, and `USER-MANUAL.md` for the current development boundary.
