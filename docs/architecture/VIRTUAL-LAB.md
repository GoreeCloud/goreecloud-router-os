# Reference Build 0.1 Virtual Network Lab

## Status

Development-only Milestone 0 test infrastructure. This lab is not a Router OS runtime, firmware image, production deployment, privileged execution adapter, firewall/NAT backend, or DHCP backend.

## Purpose

The lab provides a reproducible isolated Linux topology for validating future Reference Build 0.1 networking behavior without modifying a production network. Its initial smoke test proves only that the test harness can create an upstream namespace, router namespace, and LAN-client namespace; wire them with two veth pairs; enable IPv4 forwarding inside the router namespace; verify routed connectivity; preserve the host default route; and remove the temporary namespaces during teardown.

## Topology

`upstream namespace ↔ router namespace ↔ LAN client namespace`

The WAN-side harness uses the documentation-only TEST-NET-2 range `198.51.100.0/30`. The LAN side uses the current Reference Build 0.1 development subnet `192.168.50.0/24`. These addresses exist only inside ephemeral CI namespaces. The temporary static WAN address is lab transport plumbing and does not replace the product requirement that Reference Build 0.1 eventually exercise a DHCP WAN backend.

## Safety boundary

The lab command plan is fixed in source and accepts no caller-supplied shell fragments. Route additions use `ip -n <namespace>` and therefore target only test namespaces. The sole sysctl change is executed inside the router namespace. The harness snapshots the host default route before setup, always attempts namespace cleanup, and fails if the host default route differs after teardown or if any generated namespace remains.

The GitHub Actions job runs the lab with elevated privileges only on the ephemeral hosted runner. This is test-harness privilege, not Router OS runtime privilege and not evidence that a production least-privilege executor exists.

## Current acceptance evidence

Unit tests can verify the fixed operation plan without elevated privileges. The full namespace smoke test requires Linux network-namespace capability and is intended to run in GitHub Actions. A successful smoke test establishes the lab substrate only; it does not verify nftables policy, NAT, DHCP, configuration rollback across real daemons, management lockout recovery, Privacy Shield, Wardveil Security, Everkeep, or production networking.

## Next use

Future P0 backend work should add isolated acceptance cases to this lab incrementally. Each backend must retain its own implementation and verification status; the existence of the lab must not be treated as evidence that routing, firewall/NAT, DHCP, or management API functionality is already implemented.
