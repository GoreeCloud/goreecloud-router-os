# GoreeCloud Router OS — Feature Roadmap

Status values in this file describe repository work, not product release acceptance.

| Priority | Work item | Lifecycle | Implementation | Verification |
| --- | --- | --- | --- | --- |
| P0 | Milestone 0 configuration/state model | Development | Prototype implemented | Unit tests included |
| P0 | Deterministic configuration compiler | Development | Abstract-plan prototype implemented | Unit tests included |
| P0 | Transactional apply/verify/rollback | Development | Prototype includes atomic local journal and interrupted-state reconciliation | Automated rollback/journal/recovery tests included; production recovery not verified |
| P0 | Repository governance baseline | Development | Implemented on `main` | PR #1 CI passed and merged |
| P0 | Reference Build 0.1 virtual network lab | Planned | Not implemented | Not verified |
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

The corresponding central GoreeCloud feature-roadmap document must remain synchronized with this repository file when this roadmap materially changes.
