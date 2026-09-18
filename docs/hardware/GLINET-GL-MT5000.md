# GL.iNet Brume 3 (GL-MT5000) — Development Hardware Profile

## Status

This is a **Development hardware qualification target** for GoreeCloud Router OS.

It is not a supported device profile, bootable GoreeCloud image, installer, firmware release, or production-qualified Router OS target. Do not flash a Brume 3 based on this document or the current repository state.

Profile identity: `glinet-gl-mt5000`

Machine-readable profile: `hardware/profiles/glinet-gl-mt5000.json`

## Why this target exists

The canonical GoreeCloud Router OS specification calls for a deliberately narrow initial hardware range, including one or two approved ARM64 router platforms after the x86-64 reference work. The GL.iNet Brume 3 is being developed as an ARM64 wired-appliance qualification candidate.

A wired gateway is useful for an early physical ARM64 target because it lets Router OS validate the physical boot, storage, Ethernet, routing, firewall/NAT, DHCP, update, rollback, and recovery contracts without simultaneously requiring Wi-Fi radio and regulatory qualification.

## Vendor-reported baseline

The following values are vendor-reported facts, not GoreeCloud direct hardware observations:

- Product: Brume 3.
- Model: GL-MT5000.
- CPU: MediaTek quad-core Cortex-A53, up to 2.0 GHz.
- Memory: 1 GB DDR4.
- Internal storage: 8 GB eMMC.
- Ethernet: three ports advertised for up to 2.5 Gb/s operation.
- USB: one USB 3.0 port.
- Power: USB-C, 5 V / 3 A.
- Reset control: one reset button.
- Vendor software baseline: OpenWrt 21.02 with Linux kernel 5.4.281.

Primary vendor sources:

- https://www.gl-inet.com/products/gl-mt5000/
- https://docs.gl-inet.com/router/en/4/user_guide/gl-mt5000/

The machine-readable profile preserves these as vendor-primary evidence and deliberately keeps unverified board-specific bindings separate.

## Fail-closed profile contract

The hardware-profile validator refuses to treat a physical appliance as installable until evidence exists for the board-specific properties that can brick, strand, or misroute the device.

For the Brume 3, current blockers include:

- no direct GoreeCloud target-hardware verification;
- unknown Linux interface names and physical-port-to-netdev mapping;
- unverified eMMC partition map;
- unverified boot chain;
- unverified recovery path;
- unverified device-tree binding;
- unverified kernel support for the required board peripherals;
- unverified watchdog behavior;
- unverified thermal monitoring;
- unresolved board-specific unknowns.

A development profile is allowed to represent these unknowns. An installable profile is not.

## Hardware qualification sequence

### Phase 1 — Non-destructive hardware discovery

Before any flash or partition write:

1. Record the exact hardware revision and vendor firmware version.
2. Capture sanitized CPU, device-tree, block-device, network-interface, USB, GPIO-visible, watchdog, thermal, and kernel-module inventory.
3. Record the current eMMC partition table and filesystem types without modifying them.
4. Map the physical WAN/LAN labels to observed Linux netdevs.
5. Identify the Ethernet MAC/PHY/switch topology and whether vendor hardware offload changes packet-path semantics.
6. Identify reset-button and recovery behavior through documented, reversible procedures.
7. Determine whether a serial console or another independent recovery console is available.

Sensitive identifiers such as device-unique MAC addresses, serial numbers, credentials, keys, and tokens must not be committed to the public repository.

The repository now includes `scripts/collect_gl_mt5000_hardware.sh`, a non-mutating POSIX-shell collector intended for this phase. It reads an allowlisted set of board, CPU, device-tree, block-device, interface, watchdog, thermal, GPIO-controller, kernel-module, and tool-presence sources. It deliberately does not read interface MAC-address attributes, CPU serial values, UCI configuration, credentials, packet data, or boot-environment contents.

On a Brume 3 running vendor firmware, the intended invocation is:

```sh
sh scripts/collect_gl_mt5000_hardware.sh > gl-mt5000-discovery.txt
```

The resulting report must be reviewed locally before retention. Repository-side validation uses `prototype/routeros_m0/hardware_discovery.py`, which rejects reports containing MAC addresses, serial-number values, credential-like fields, a missing privacy boundary, or missing non-mutation assertions.

The collector writes only to stdout. Redirecting stdout to a report file is an operator-selected local file write; the collector itself does not change router configuration, boot state, storage layout, firmware, firewall state, or network state.

### Phase 2 — Recovery proof

Before a GoreeCloud image may write internal storage:

1. Establish a documented recovery path that does not depend on the candidate Router OS image being healthy.
2. Verify recovery on the actual target device.
3. Preserve enough vendor or GoreeCloud recovery material to restore a bootable state.
4. Determine which boot and partition metadata can safely be changed.
5. Test power interruption and failed-boot behavior in a controlled acceptance procedure.

No ordinary development convenience may substitute for this gate.

### Phase 3 — Kernel and board enablement

Build a reproducible ARM64 kernel/userspace target with:

- accepted device-tree support;
- all three Ethernet paths;
- eMMC;
- USB;
- reset/recovery controls where exposed safely;
- watchdog where available;
- thermal monitoring;
- required nftables/Netfilter facilities;
- network namespaces and forwarding;
- required cryptographic primitives;
- required persistent-state filesystems.

Missing required functionality must fail closed.

### Phase 4 — Storage and update architecture

Define the Brume 3 system/data/recovery layout only after the existing eMMC and boot chain are understood.

The Router OS specification prefers safe update and rollback behavior, including A/B system partitions where supported. The GL-MT5000 profile must not assume A/B partitioning is safe until the board's real boot and storage constraints are verified.

### Phase 5 — Router OS runtime binding

Bind the canonical Router OS product model to the qualified hardware profile:

- deterministic WAN/LAN interface roles;
- DHCP WAN;
- static LAN;
- IPv4/IPv6 forwarding as included by release scope;
- nftables firewall and NAT;
- LAN DHCP;
- local authenticated management;
- capability reporting;
- transactional apply/verify/rollback;
- persistent recovery state;
- privacy-safe diagnostics.

Board-specific mechanics must remain behind hardware/deployment adapters rather than forking the Router OS configuration model.

### Phase 6 — Physical acceptance

The GL-MT5000 may move toward Supported only after device-level evidence covers at least:

- first boot and repeated reboot;
- all Ethernet ports at required link modes;
- routing and forwarding;
- firewall and NAT behavior;
- DHCP;
- management lockout prevention and recovery;
- upgrade and rollback;
- backup/restore;
- eMMC integrity and power-loss recovery;
- sustained load;
- thermal behavior;
- watchdog/reset behavior;
- host/device safety invariants;
- applicable platform-system conformance.

## Current implementation slice

The current repository slice adds:

- `hardware/profiles/glinet-gl-mt5000.json` with vendor-primary facts and explicit unknowns;
- `prototype/routeros_m0/hardware_profile.py` with fail-closed profile validation and readiness assessment;
- `tests/test_hardware_profile.py` with Development-state, architecture, resource, port-identity, and installability safety tests;
- `scripts/collect_gl_mt5000_hardware.sh` with an allowlisted non-mutating discovery path designed for stock vendor firmware;
- `prototype/routeros_m0/hardware_discovery.py` with privacy/status validation for retained discovery evidence;
- `tests/test_gl_mt5000_discovery.py` with fixture-based collection, privacy rejection, non-mutation boundary, and forbidden-command source tests.

This slice does not modify hardware, build a kernel, produce an image, or install Router OS.

## Next engineering gate

Run the collector on an actual Brume 3 while it remains on vendor firmware, review the report locally for privacy, validate it with the repository parser, and use the resulting direct-observation evidence to resolve only the hardware-profile fields actually demonstrated. Physical port mapping, boot/recovery behavior, and any action that could change eMMC or boot state remain separate controlled tests.
