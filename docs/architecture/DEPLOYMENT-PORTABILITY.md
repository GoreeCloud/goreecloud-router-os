# GoreeCloud Router OS — Deployment Portability Contract

## Status

This document records a planned product requirement and Development architecture contract. It does **not** state that any Router OS installation profile is currently released, supported, production-qualified, or Stable.

## Objective

GoreeCloud Router OS must be deployable across multiple qualified execution environments without changing the Router OS product contract. Installation method may change packaging, device attachment, privilege plumbing, lifecycle integration, and host-specific adapters; it must not create incompatible Router OS products with different configuration semantics, policy behavior, APIs, administrative experience, backup/restore meaning, or safety expectations.

The initial required deployment families are:

- Proxmox VE virtual machine.
- Generic KVM/QEMU virtual machine.
- Docker using a qualified OCI image/profile.
- Podman using a qualified OCI image/profile.
- GoreeCloud Containers using the GoreeCloud Container Engine when that platform provides the required accepted runtime capabilities.
- Bare-metal x86-64 appliance installation.
- Other qualified virtual-machine, cloud-VM, system-container, and hardware targets added through the same acceptance process.

Additional platforms may be added only after their capability and acceptance evidence is defined. A platform name alone is not evidence of support.

## Canonical product contract

Every supported deployment profile must consume the same canonical Router OS configuration/state model and expose materially equivalent supported behavior for:

- Configuration validation, revision identity, preview, apply, verification, retention, and rollback.
- Routing, firewall, NAT, DHCP, DNS-distribution integration, VPN/private-network integration, and other capabilities included in the applicable Router OS release scope.
- Local authenticated administration and the applicable Glaze UI experience.
- Privacy Shield, Wardveil Security, Everkeep, Identity, Manager, Mesh, Network/Conduit, and Beacon boundaries when those integrations become accepted for that release.
- Upgrade, backup, restore, export, import, migration, diagnostics, and evidence-backed health/status behavior.

Environment-specific packaging must remain behind explicit adapter boundaries. The canonical configuration must not contain Docker-only, Podman-only, Proxmox-only, or host-vendor-only assumptions except within a clearly scoped deployment profile or adapter block.

## Deployment profiles

### Full virtual-machine profile

The full VM profile should be the reference environment for early complete-router acceptance. It should support direct or bridged virtual NIC attachment, normal Linux kernel networking, nftables, network namespaces where required internally, persistent system storage, controlled boot/update behavior, and recovery access.

Proxmox VE is a required VM target. Generic KVM/QEMU must remain compatible with the same virtual-hardware assumptions where practical so Proxmox support does not become a proprietary dependency.

### OCI container profile

Docker, Podman, and GoreeCloud Containers should consume the same Router OS OCI artifact where practical. The OCI profile must declare and verify the exact Linux capabilities, namespace access, devices, sysctls, mounts, persistent state, and network attachment required by the selected Router OS feature set.

The full-router container profile must not default to unrestricted `--privileged` operation merely for convenience. Required capabilities should be minimized and documented. If a requested Router OS feature cannot operate safely under the available container-runtime/kernel boundary, startup must fail closed with a specific capability diagnostic rather than silently disabling security or networking behavior.

Rootless execution is desirable for management-only or otherwise compatible workloads, but a full router instance must not be advertised as rootless-capable until nftables, interface ownership, forwarding, DHCP, VPN/tunnel devices, and other required kernel operations are independently accepted in that mode.

### GoreeCloud Containers profile

The canonical platform identity is **GoreeCloud Containers**, with **GoreeCloud Container Engine** as its backend. Router OS integration must use accepted GoreeCloud Containers APIs/capabilities rather than depending on undocumented engine internals.

Until GoreeCloud Containers has accepted networking, persistence, runtime, privilege, and recovery behavior sufficient for Router OS, the Router OS GoreeCloud Containers profile remains Planned. Docker remains an interoperability target and current GoreeCloud production container-runtime authority until the Containers project separately changes that state.

### Bare-metal appliance profile

The bare-metal profile should provide a bootable/installable Router OS image for qualified hardware, with deterministic interface discovery, persistent system/data partitions, recovery environment, safe updates, hardware capability detection, and explicit driver/firmware requirements.

Hardware-specific support must be qualified per device or capability class rather than inferred from generic Linux compatibility.

### Cloud and additional virtualization profiles

Cloud VM, VMware-compatible, Hyper-V-compatible, system-container, or other environments may be supported when their networking model can satisfy Router OS isolation, forwarding, firewall/NAT, persistence, recovery, and administrative-safety requirements. These profiles must use the same conformance and status-integrity rules as the initial targets.

## Network attachment abstraction

Router OS must represent WAN/LAN/VLAN roles independently from host-specific attachment mechanics. Deployment adapters may map logical interfaces to supported mechanisms including:

- Physical NICs.
- virtio or comparable VM NICs.
- TAP devices.
- Linux bridges.
- veth pairs.
- macvlan/ipvlan where their isolation semantics are acceptable.
- VLAN trunks.
- Runtime-provided OCI network attachments.

The adapter must surface the observed attachment and capabilities. It must not claim a logical WAN/LAN is operational merely because a configuration object exists.

## Persistent state and migration

All supported profiles must provide explicit durable locations for Router OS configuration, transaction/recovery data, certificates/keys or secret references, logs/diagnostics subject to Privacy Shield, package/update state, and other applicable durable product data.

Disposable container layers must never become the sole copy of important Router OS state. OCI deployments should use named volumes, managed persistent storage, or another accepted durable mechanism. VM and bare-metal profiles should use explicit durable partitions/volumes.

Backup/export artifacts should be portable across deployment profiles when hardware- or environment-specific bindings are not required. Migration between Docker, Podman, GoreeCloud Containers, Proxmox VM, generic VM, and bare metal should preserve canonical configuration and user-owned durable state while re-running capability detection and environment binding.

## Capability negotiation and fail-closed behavior

At installation/startup, Router OS should build a capability report covering at least:

- Required kernel networking primitives.
- nftables/Netfilter availability and version compatibility.
- Network-interface ownership/attachment.
- IPv4/IPv6 forwarding controls.
- DHCP service binding requirements.
- TUN/tunnel support where required.
- Required Linux capabilities and security-module restrictions.
- Persistent storage availability and permissions.
- Time, entropy, and cryptographic prerequisites.
- Update/recovery support.

A deployment profile must refuse activation when a required capability for the selected configuration is unavailable. Optional capabilities may be disabled only when the user-visible status clearly identifies the limitation and the missing capability is not required by the active configuration or security contract.

## Packaging and lifecycle

The build/release system should produce traceable artifacts from one accepted source revision. Depending on target, this may include:

- OCI multi-architecture images and runtime manifests.
- Proxmox/generic VM disk images or installer media.
- Bare-metal installer/recovery images.
- Cloud images where justified.
- Environment-specific deployment descriptors/templates.

Every artifact must retain source revision, release identity, dependency/SBOM/provenance information, and compatible migration/rollback expectations. Environment-specific packaging must not fork the product implementation into permanently divergent codebases.

## Cross-environment acceptance matrix

A deployment profile is not Supported merely because Router OS starts. Each claimed profile must pass the applicable shared acceptance suite, including:

1. Install/create and first boot/start.
2. Capability detection and fail-closed negative tests.
3. Canonical configuration import and revision identity.
4. Interface binding and observed-state verification.
5. Routing and forwarding.
6. Stateful firewall behavior.
7. NAT/masquerade behavior where applicable.
8. DHCP and address-assignment behavior where applicable.
9. Local authenticated administration and management-lockout recovery.
10. Transactional apply, rollback, restart, crash, and recovery tests.
11. Upgrade and rollback.
12. Backup/export, restore/import, and cross-environment migration.
13. Privacy-safe diagnostics and secret handling.
14. Resource limits and performance baselines appropriate to the environment.
15. Host-safety checks proving the deployment does not mutate unrelated host routing/firewall/network state.
16. Required GoreeCloud platform-system conformance for the release.

The same test vectors should be reused across profiles wherever the environment permits so behavioral drift is detectable.

## Quality requirement

The target is deployment-method transparency for ordinary administration: after successful installation and qualification, users should interact with the same Router OS concepts and receive the same supported product behavior regardless of whether the instance runs on Proxmox, Docker, Podman, GoreeCloud Containers, bare metal, or another accepted environment.

“Works flawlessly” is therefore treated as an acceptance obligation rather than a marketing claim. A deployment profile may be called Supported only when its required behavior is implemented and verified. Planned or partially validated profiles must remain labeled Planned, Experimental, Development, or otherwise non-Stable as appropriate.

## Current implementation boundary

As of the current Milestone 0 source state, no installable Router OS appliance, OCI image, Proxmox image/template, bare-metal installer, or production deployment package is accepted. The existing namespace lab and bounded privileged adapter are development/acceptance substrates only.

The deployment-portability requirement is an active planned implementation obligation and must remain synchronized with the canonical Drive specification, repository/Drive feature roadmaps, task tracking, and future implementation evidence.
