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

## Current product-source scope

The repository currently implements only an **unprivileged Router OS architecture prototype**:

1. Candidate configuration parsing.
2. Cross-field validation for interface identity, subnets, management exposure, forwarding intent, and DHCP scope.
3. Canonical normalization and SHA-256 revision identity.
4. Deterministic compilation to an abstract execution plan.
5. Deterministic privacy-safe change preview with bounded risk classification for the current Reference Build 0.1 schema.
6. Review/apply consistency binding the preview to the exact previous and desired revisions before the reviewed orchestration path delegates to apply.
7. In-memory transactional apply, verify, retain, and rollback behavior.
8. Optional atomic local transaction journaling for prepared/applied/terminal phase transitions.
9. Fail-closed interrupted-operation reconciliation against exact previous and desired revisions.
10. Tests that prove the current validation, preview, review/apply, transaction, journal-integrity, recovery, and lab-plan safety semantics.

No **product prototype** action executes `nft`, `ip`, `tc`, `sysctl`, `hostapd`, DHCP daemons, WireGuard, FRRouting, Suricata, or another privileged system command. A separate development test harness is described below and must not be confused with the product runtime.

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

The Milestone 0 preview produces bounded semantic change descriptions, an overall risk level, a connectivity-confirmation indicator for high/critical changes, and an approval token derived from the exact previous/desired revision pair and preview content. The reviewed transaction path recomputes that preview immediately before apply and refuses a stale candidate or stale previous state before runtime mutation.

Apply, verify, retain, rollback, journaling, and interrupted recovery still operate only against an in-memory product adapter. Privileged Linux Router OS adapters are future work and require separate safety review and acceptance.

## Recovery proof boundary

The Milestone 0 journal is a local development mechanism, not an Everkeep implementation. It stores only the current secret-free prototype configuration, rejects defined sensitive field names, writes an integrity checksum, and uses temp-file fsync plus atomic replacement. The unkeyed checksum detects corruption/consistency failures but is not an adversarial tamper-proof signature.

Recovery accepts an exact previous revision as evidence that no candidate apply remains active, or an exact desired revision as evidence that the candidate state is already observed. A corrupt journal or a runtime state matching neither exact revision is preserved and surfaced as `RecoveryRequired`; the prototype does not overwrite an unknown third state automatically.

This behavior proves process-level decision semantics only. It does not establish real filesystem power-loss guarantees, kernel/network-daemon rollback, hardware recovery, production secret handling, or accepted Everkeep recovery.

## Preview proof boundary

The current preview intentionally summarizes only known fields from the narrow Reference Build 0.1 model. It does not echo raw configuration values or unknown fields into its report, so secret-like extension values are not surfaced by the preview. Its risk levels are development classifications, not Wardveil Security findings or production safety certification.

A high or critical preview merely indicates that the later product should require stronger confirmation/recovery behavior; it does not prove that a real network lockout can already be detected or recovered from.

## Virtual network lab boundary

The repository includes a development-only Reference Build 0.1 Linux network-namespace lab. The initial harness creates three generated namespaces representing upstream, router, and LAN client; connects them with two veth pairs; uses documentation-only WAN test addressing plus the current development LAN subnet; enables IPv4 forwarding inside the router namespace; verifies routed ping connectivity; compares the host default route before and after execution; and verifies namespace teardown.

The lab runs with elevated privileges on an ephemeral GitHub-hosted CI runner because Linux namespace creation requires them. Those privileges belong to the isolated test harness, not the Router OS product runtime. The lab command plan accepts no caller-supplied shell fragments, and all route additions target explicit namespaces rather than the host routing table.

The initial namespace lab is an acceptance substrate only. Its temporary static WAN plumbing does not satisfy the Reference Build 0.1 DHCP-WAN requirement, and it does not implement or verify the planned Router OS privileged execution adapter, nftables firewall/NAT backend, LAN DHCP backend, authenticated management API, management-lockout recovery, or platform-system integrations.

## Canonical authority

The controlling product specification is the canonical Drive document. This repository file must remain consistent with it but does not replace it.
