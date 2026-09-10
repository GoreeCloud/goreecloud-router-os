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

## Current configuration and transaction scope

The repository currently implements a Development Router OS architecture core for:

1. Candidate configuration parsing.
2. Cross-field validation for interface identity, subnets, management exposure, forwarding intent, and DHCP scope.
3. Canonical normalization and SHA-256 revision identity.
4. Deterministic compilation to an abstract execution plan.
5. Deterministic privacy-safe change preview with bounded risk classification for the current Reference Build 0.1 schema.
6. Review/apply consistency binding the preview to the exact previous and desired revisions before the reviewed orchestration path delegates to apply.
7. In-memory transactional apply, verify, retain, and rollback behavior.
8. Optional atomic local transaction journaling for prepared/applied/terminal phase transitions.
9. Fail-closed interrupted-operation reconciliation against exact previous and desired revisions.
10. Tests that prove the current validation, preview, review/apply, transaction, journal-integrity, recovery, lab, and adapter safety semantics.

The transaction core still uses `InMemoryRuntime` and does not invoke the privileged namespace adapter.

## State model

The engineering architecture distinguishes candidate, desired, applied, and observed state. The prototype preserves that distinction and does not equate intent with successful runtime application.

## Safe configuration lifecycle

The intended lifecycle remains:

`Draft → Validate → Preview → Apply → Verify → Retain or Roll Back`

The Milestone 0 preview produces bounded semantic change descriptions, an overall risk level, a connectivity-confirmation indicator for high/critical changes, and an approval token derived from the exact previous/desired revision pair and preview content. The reviewed transaction path recomputes that preview immediately before apply and refuses a stale candidate or stale previous state before runtime mutation.

Apply, verify, retain, rollback, journaling, and interrupted recovery still operate against the in-memory transaction adapter. Real privileged transactional integration requires separate backend-specific snapshot, observation, rollback/compensation, and recovery acceptance.

## Recovery proof boundary

The Milestone 0 journal is a local development mechanism, not an Everkeep implementation. It stores only the current secret-free prototype configuration, rejects defined sensitive field names, writes an integrity checksum, and uses temp-file fsync plus atomic replacement. The unkeyed checksum detects corruption/consistency failures but is not an adversarial tamper-proof signature.

Recovery accepts an exact previous revision as evidence that no candidate apply remains active, or an exact desired revision as evidence that the candidate state is already observed. A corrupt journal or a runtime state matching neither exact revision is preserved and surfaced as `RecoveryRequired`; the prototype does not overwrite an unknown third state automatically.

This behavior proves process-level decision semantics only. It does not establish real filesystem power-loss guarantees, kernel/network-daemon rollback, hardware recovery, production secret handling, or accepted Everkeep recovery.

## Preview proof boundary

The current preview intentionally summarizes only known fields from the narrow Reference Build 0.1 model. It does not echo raw configuration values or unknown fields into its report, so secret-like extension values are not surfaced by the preview. Its risk levels are development classifications, not Wardveil Security findings or production safety certification.

A high or critical preview merely indicates that the later product should require stronger confirmation/recovery behavior; it does not prove that a real network lockout can already be detected or recovered from.

## Virtual network lab boundary

The repository includes a Development-only Reference Build 0.1 Linux network-namespace lab. It creates generated upstream/router/LAN-client namespaces, connects them with veth pairs, enables IPv4 forwarding inside the router namespace, verifies routed ping connectivity, compares the host default route before and after execution, and verifies namespace teardown.

The lab runs with elevated privileges on an ephemeral GitHub-hosted CI runner because Linux namespace creation requires them. Those privileges belong to the isolated test harness, not a production Router OS runtime.

## Privileged Linux adapter boundary

The repository now contains a separate `LinuxNamespaceExecutionAdapter` Development substrate. It accepts only dedicated `gcr-a-<digits>` namespaces, requires an explicit interface allowlist, preflights the complete plan before target probes or mutation, requires root only after successful plan validation, resolves absolute Linux tool paths, and executes structured argv without shell interpretation.

The accepted operation subset is limited to static IPv4 LAN address/link configuration and `net.ipv4.ip_forward` inside the approved namespace. The complete compiler output is intentionally rejected because WAN DHCP, `dhcp.intent`, `firewall.intent`, and `management.intent` remain unsupported.

This adapter is not integrated with `apply_transaction`, is not a host-network or physical-router executor, and does not establish production least privilege, rollback, nftables/NAT, DHCP, management safety, platform-system integration, or hardware acceptance.

## Canonical authority

The controlling product specification is the canonical Drive document. This repository file must remain consistent with it but does not replace it.
