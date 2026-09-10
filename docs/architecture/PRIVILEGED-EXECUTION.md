# Privileged Linux Execution Boundary — Milestone 0

## Status

Development-only execution substrate for Reference Build 0.1. This is not a production router executor, firmware privilege model, firewall/NAT backend, DHCP backend, management service, or hardware acceptance result.

## Purpose

The Milestone 0 configuration compiler emits structured abstract operations. `LinuxNamespaceExecutionAdapter` begins the separate execution layer by accepting only a deliberately tiny subset of those operations inside an isolated Linux network namespace.

The current adapter exists to prove that Router OS can cross from structured intent to observed Linux state without introducing arbitrary shell execution or broad host-network authority.

## Accepted target boundary

Execution is restricted to namespace names matching `gcr-a-<digits>` and to interface names supplied through an explicit adapter allowlist. The adapter never targets the host namespace.

Before mutation, the complete submitted plan is preflighted. An unsupported operation rejects the whole plan before root checks, target probes, or command execution. The adapter then verifies root execution, resolves absolute `ip` and `sysctl` tool paths, verifies that the approved namespace exists, and verifies each required allowlisted interface exists inside that namespace.

## Currently supported operations

The current tranche supports only:

- Static IPv4 configuration of the Reference Build LAN interface using namespace-scoped `ip addr replace`.
- Bringing that allowlisted LAN interface up inside the namespace.
- Setting `net.ipv4.ip_forward` to integer `0` or `1` through `ip netns exec` inside the same namespace.

Commands are materialized as structured argv and executed with `shell=False` semantics. User-controlled shell fragments, interpreters, arbitrary sysctls, arbitrary namespaces, and arbitrary interface names are not accepted.

## Explicitly unsupported operations

The compiler's complete Reference Build 0.1 plan is intentionally not executable yet. WAN DHCP interface configuration, `dhcp.intent`, `firewall.intent`, and `management.intent` have no accepted privileged backend in this tranche and therefore fail closed.

The adapter also does not implement routing-table mutation, nftables, NAT, DHCP service lifecycle, DNS, Wi-Fi, VPN, traffic control, FRRouting, Suricata, package management, updates, host networking, physical-interface ownership, or production recovery.

## Transaction boundary

The adapter is not wired into `apply_transaction`. The existing transaction proof still uses `InMemoryRuntime`. Real Router OS transaction integration must wait until the required networking backends have defined snapshot, observed-state verification, rollback/compensation, failure handling, and recovery semantics.

This separation prevents a partially implemented privileged layer from being mistaken for complete transactional apply behavior.

## CI acceptance

`lab/privileged_adapter_smoke.py` creates one disposable `gcr-a-<pid>` namespace and a dummy LAN interface, derives the static LAN address and forwarding intent from the current compiled reference configuration, executes only the supported adapter subset, observes the resulting address/link/forwarding state, removes the namespace, and checks that the host default route is unchanged.

Unit tests separately require that the full reference plan is rejected before any runner call, unsafe targets are rejected, unsupported backend kinds fail closed, only the approved sysctl is accepted, and execution materializes absolute tool paths.

CI evidence validates only this isolated Development boundary. It does not establish production least privilege, firewall/NAT/DHCP behavior, real-router rollback, management safety, hardware qualification, Platform System acceptance, release eligibility, or Stable status.

## Next backend sequence

The next P0 implementation should add the nftables firewall/NAT backend and its isolated observed-state acceptance cases before broader product execution is enabled. LAN DHCP and authenticated management execution remain separate gates and must retain independent verification state.
