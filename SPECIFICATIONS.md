# GoreeCloud Router OS — Repository Specifications

## Lifecycle

- Product status: Proposed.
- Repository lifecycle: Development.
- Current engineering stage: Milestone 0 proof-of-architecture.
- Production status: Not released, not deployed, not production-qualified.

## Product boundary

GoreeCloud Router OS is intended to own local and edge-network routing, firewalling, NAT, segmentation, device policy, WAN/LAN behavior, and router administration. It does not supersede GoreeCloud Identity, Gateway, Network/Conduit, Beacon, Wardveil Security, Privacy Shield, Everkeep, Glaze UI, Mesh, or Manager authority.

## Reference Build 0.1 target

The first executable reference build is intended for a narrow x86-64 virtual-router environment with one DHCP WAN and one static LAN. Its minimum target includes IPv4 forwarding, LAN DHCP, stateful nftables firewalling, apply verification, known-good rollback, a local authenticated management API, a minimal Glaze UI surface, local recovery, privacy-safe diagnostics, and evidence-backed subsystem status.

Wi-Fi, multi-WAN, IDS/IPS, dynamic routing, extension installation, high availability, arbitrary consumer-router support, and production remote administration are outside Reference Build 0.1 unless separately approved.

## Current source scope

The repository currently implements only an **unprivileged architecture prototype**:

1. Candidate configuration parsing.
2. Cross-field validation for interface identity, subnets, management exposure, forwarding intent, and DHCP scope.
3. Canonical normalization and SHA-256 revision identity.
4. Deterministic compilation to an abstract execution plan.
5. In-memory transactional apply, verify, retain, and rollback behavior.
6. Tests that prove the current prototype semantics.

No prototype action executes `nft`, `ip`, `tc`, `sysctl`, `hostapd`, DHCP daemons, WireGuard, FRRouting, Suricata, or another privileged system command.

## State model

The engineering architecture distinguishes:

- Candidate state: proposed configuration submitted for validation.
- Desired state: validated configuration accepted as intended target state.
- Applied state: configuration a runtime adapter reports as applied.
- Observed state: independently read runtime state used for verification.

The prototype preserves that distinction and does not equate intent with successful runtime application.

## Safe configuration lifecycle

The intended lifecycle remains:

`Draft → Validate → Preview → Apply → Verify → Retain or Roll Back`

The current prototype implements Validate, Preview, Apply, Verify, Retain, and Roll Back only against an in-memory adapter. Privileged Linux adapters are future work and require separate safety review and acceptance.

## Canonical authority

The controlling product specification is the canonical Drive document. This repository file must remain consistent with it but does not replace it.
