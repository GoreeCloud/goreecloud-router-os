# GoreeCloud Router OS — Features and Implementation State

## Implemented in the Milestone 0 prototype

- JSON candidate configuration loading.
- Two-interface Reference Build 0.1 validation.
- Unique logical/physical interface identity checks.
- IPv4 subnet parsing and overlap rejection.
- WAN DHCP requirement for the current reference profile.
- Static LAN subnet and DHCP-pool containment checks.
- Management-plane WAN-binding rejection.
- Required default-deny firewall intent for the reference profile.
- Deterministic normalized configuration and revision digest.
- Deterministic abstract execution-plan compilation.
- Deterministic privacy-safe configuration change preview with none/low/medium/high/critical risk classification.
- Preview warnings for LAN address/interface changes, firewall changes, management-plane changes, DHCP changes, routing changes, and initial configuration.
- Review/apply consistency token bound to the exact previous and desired configuration revisions.
- Refusal to apply through the reviewed orchestration path when the reviewed preview becomes stale, without mutating runtime state.
- In-memory transactional apply and observed-state verification.
- Automatic rollback to the previous known-good state on failed verification.
- Optional atomic local transaction journaling across prepared, applied, retained, and rolled-back phases.
- Journal checksum/digest consistency checks and restrictive POSIX file permissions.
- Explicit refusal to persist defined sensitive configuration fields in the Milestone 0 journal.
- Interrupted-transaction reconciliation that accepts only exact desired/previous revisions and refuses unknown third states.
- Preservation of corrupt/ambiguous journal evidence for explicit recovery instead of automatic overwrite.
- Unit tests for validation, determinism, preview/review consistency, state separation, rollback, journal integrity, interrupted recovery, and virtual-lab plan safety.

## Implemented development test infrastructure

- Reference Build 0.1 Linux network-namespace lab scaffold with upstream, router, and LAN-client namespaces.
- Two temporary veth links and namespace-local addressing/routing for a routed-connectivity smoke test.
- Router-namespace-only IPv4-forwarding enablement.
- Host-default-route before/after comparison and explicit namespace teardown verification.
- GitHub Actions execution of the isolated namespace smoke test on an ephemeral hosted runner.

The virtual lab is test infrastructure, not Router OS runtime functionality. Its temporary static WAN plumbing does not implement the specified DHCP-WAN backend.

## Specified but not implemented

The canonical specification defines production routing, nftables-backed firewalling, NAT, VLANs, device inventory and quarantine, WAN/multi-WAN, Wi-Fi and travel-router functions, GoreeCloud Network/Conduit integration, VPN interoperability, Beacon integration, DHCP/IPv6, SQM, traffic visibility, IDS/IPS, Wardveil Security, Privacy Shield, Everkeep, Glaze UI administration, diagnostics, extensions, API/CLI, secure updates, hardware support, and high availability.

These capabilities remain planned or later-milestone work. The local journal is not Everkeep integration, the preview risk model is limited to the current narrow Reference Build 0.1 schema, the namespace lab is not a product privileged executor, and the recovery proof does not establish production crash/power-loss safety. Specified capabilities must not be interpreted as current repository functionality.
