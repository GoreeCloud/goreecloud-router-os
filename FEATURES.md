# GoreeCloud Router OS — Features and Implementation State

## Implemented in the Milestone 0 configuration/transaction core

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

## Implemented Development test and execution infrastructure

- Reference Build 0.1 Linux network-namespace lab scaffold with upstream, router, and LAN-client namespaces.
- Two temporary veth links and namespace-local addressing/routing for a routed-connectivity smoke test.
- Router-namespace-only IPv4-forwarding enablement.
- Host-default-route before/after comparison and explicit namespace teardown verification.
- Bounded `LinuxNamespaceExecutionAdapter` restricted to `gcr-a-<digits>` namespaces and an explicit interface allowlist.
- Complete adapter-plan preflight before target probes or mutation.
- Structured-argv static IPv4 LAN address replacement and link-up execution inside the approved namespace.
- Structured-argv `net.ipv4.ip_forward` execution inside the approved namespace, limited to integer 0/1.
- Absolute `ip`/`sysctl` tool resolution before privileged execution.
- Fail-closed refusal of WAN DHCP and unimplemented DHCP, firewall, and management operation kinds.
- Unit tests proving full-plan refusal before runner activity, target validation, sysctl restrictions, tool-path materialization, and non-root refusal.
- GitHub Actions smoke tests for both the virtual topology and the isolated namespace adapter on an ephemeral hosted runner.

The namespace lab and privileged adapter are Development infrastructure, not a deployable Router OS runtime. The adapter is not wired into product transaction apply/rollback, and the temporary lab WAN plumbing does not implement the specified DHCP-WAN backend.

## Specified but not implemented

The canonical specification defines production routing, nftables-backed firewalling, NAT, VLANs, device inventory and quarantine, WAN/multi-WAN, Wi-Fi and travel-router functions, GoreeCloud Network/Conduit integration, VPN interoperability, Beacon integration, DHCP/IPv6, SQM, traffic visibility, IDS/IPS, Wardveil Security, Privacy Shield, Everkeep, Glaze UI administration, diagnostics, extensions, API/CLI, secure updates, hardware support, and high availability.

These capabilities remain planned or later-milestone work. The local journal is not Everkeep integration, the preview risk model is limited to the current narrow Reference Build 0.1 schema, the namespace adapter implements only its explicitly bounded operations, and the recovery proof does not establish production crash/power-loss safety. Specified capabilities must not be interpreted as current repository functionality.
