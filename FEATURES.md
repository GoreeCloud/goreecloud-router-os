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
- In-memory transactional apply and observed-state verification.
- Automatic rollback to the previous known-good state on failed verification.
- Unit tests for validation, determinism, state separation, and rollback.

## Specified but not implemented

The canonical specification defines routing, nftables-backed firewalling, NAT, VLANs, device inventory and quarantine, WAN/multi-WAN, Wi-Fi and travel-router functions, GoreeCloud Network/Conduit integration, VPN interoperability, Beacon integration, DHCP/IPv6, SQM, traffic visibility, IDS/IPS, Wardveil Security, Privacy Shield, Everkeep, Glaze UI administration, diagnostics, extensions, API/CLI, secure updates, hardware support, and high availability.

These capabilities remain planned or later-milestone work. They must not be interpreted as current repository functionality.
