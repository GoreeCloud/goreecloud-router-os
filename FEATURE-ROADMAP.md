# GoreeCloud Router OS — Feature Roadmap

Status values in this file describe repository work, not product release acceptance.

| Priority | Work item | Lifecycle | Implementation | Verification |
| --- | --- | --- | --- | --- |
| P0 | Milestone 0 configuration/state model | Development | Prototype implemented | Unit tests included |
| P0 | Deterministic configuration compiler | Development | Abstract-plan prototype implemented | Unit tests included |
| P0 | Safe configuration preview and review/apply consistency | Development | Privacy-safe deterministic preview and exact previous/desired review token implemented | PR #5 CI passed with 32 tests and reference-config validation; production management-lockout recovery not verified |
| P0 | Transactional apply/verify/rollback | Development | Prototype includes atomic local journal and interrupted-state reconciliation | Automated rollback/journal/recovery tests included; production recovery not verified |
| P0 | Repository governance baseline | Development | Implemented on `main` | PR #1 CI passed and merged |
| P0 | Reference Build 0.1 virtual network lab | Development | Isolated Linux namespace/veth topology scaffold and routed smoke test implemented | PR #6 CI passed: 38 unit tests, reference-config validation, routed ping with 0% packet loss, host default route unchanged, and generated namespaces removed; product routing/firewall/NAT/DHCP acceptance remains unverified |
| P0 | Privileged Linux execution adapter | Planned | Not implemented | Not verified |
| P0 | nftables firewall/NAT backend | Planned | Not implemented | Not verified |
| P0 | LAN DHCP backend | Planned | Not implemented | Not verified |
| P0 | Local authenticated management API | Planned | Not implemented | Not verified |
| P1 | Minimal Glaze UI administration surface | Planned | Not implemented | Not verified |
| P1 | Everkeep-backed durable snapshots/recovery | Planned | Local journal/recovery proof only; Everkeep not integrated | Not accepted or production-verified |
| P1 | Privacy Shield authorization/retention enforcement | Planned | Not implemented | Not verified |
| P1 | Wardveil evidence and security-state integration | Planned | Not implemented | Not verified |
| P1 | Network/Conduit and Beacon integration contracts | Planned | Not implemented | Not verified |
| P2 | VLANs, policy routing, multi-WAN, SQM | Planned | Not implemented | Not verified |
| P2 | Wi-Fi and travel-router hardware workflows | Planned | Not implemented | Not verified |
| P3 | IDS/IPS, dynamic routing, extensions, HA | Future | Not implemented | Not verified |

## Immediate development gate

Reference Build 0.1 must remain a development artifact until routing, firewall, NAT, DHCP, configuration transaction, rollback, recovery, and management-safety behavior pass applicable automated and virtual-machine acceptance tests.

The virtual network lab is only the acceptance substrate. Its verified smoke test must not be treated as implementation evidence for the still-planned Router OS privileged execution, firewall/NAT, DHCP, or management API backends.

The corresponding central GoreeCloud feature-roadmap document must remain synchronized with this repository file when this roadmap materially changes.
