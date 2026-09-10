# GoreeCloud Router OS — Security

## Security status

The current repository is a Development / Milestone 0 prototype. It is not a production firewall, security appliance, VPN gateway, or hardened router distribution.

## Current trust boundary

The configuration/transaction core performs local parsing, validation, hashing, abstract plan generation, privacy-safe preview/review checks, in-memory transaction simulation, and optional local transaction journaling. That core does not execute privileged system commands or modify network state.

Separate Development-only privileged code exists for isolated CI acceptance. The virtual network lab creates temporary namespaces/veths and proves routed topology/teardown. The bounded `LinuxNamespaceExecutionAdapter` targets only dedicated `gcr-a-<digits>` namespaces and explicit allowlisted interfaces and currently executes only static LAN address/link state plus namespace-scoped IPv4 forwarding. Neither component is a production Router OS privilege boundary.

The journal is intentionally restricted to the current secret-free prototype configuration. It is not a credential store, Everkeep implementation, or security attestation mechanism.

## Security invariants enforced now

- Management binding to the WAN role is rejected by the reference profile.
- The current reference profile requires a default-deny firewall intent.
- WAN and LAN interface identities must be distinct.
- Configured IPv4 subnets must not overlap.
- LAN DHCP pools must remain inside the LAN subnet and exclude the router address.
- Privacy-safe previews do not echo raw configuration objects or unknown extension values.
- Reviewed apply refuses a stale previous/desired preview pair before runtime mutation.
- Transaction verification failure triggers rollback to the previous mock known-good state.
- Journal persistence rejects defined sensitive field names and uses restrictive POSIX permissions.
- Journal reads fail closed on malformed content, unexpected fields, digest mismatches, or checksum mismatches.
- Interrupted recovery automatically accepts only exact previous/desired revisions; unknown third states are not overwritten.
- Virtual-lab route modifications target named namespaces and the lab verifies host-route invariance and teardown.
- Privileged-adapter namespaces must match `gcr-a-<digits>` and interfaces must be explicitly allowlisted with safe Linux-length names.
- The adapter preflights the entire plan before root checks, target probes, or mutation; unsupported operations therefore cannot produce partial execution.
- The adapter accepts no arbitrary shell command, interpreter, sysctl, route operation, or host namespace target.
- Privileged commands use structured argv and resolved absolute `ip`/`sysctl` paths.
- The complete Reference Build plan remains unexecutable because WAN DHCP, DHCP service, firewall/NAT, and management backends are absent.

The journal checksum is unkeyed and should be understood as corruption/consistency detection, not protection against an attacker who can rewrite both content and checksum.

## Privileged Development boundary

The adapter smoke test creates a disposable namespace and dummy interface on an ephemeral GitHub-hosted runner, applies only the accepted static-LAN and forwarding subset, observes resulting state, removes the namespace, and checks that the host default route did not change.

Repository workflow permissions remain `contents: read` and the smoke path does not require repository secrets. Running with root inside a disposable CI runner proves only the reviewed namespace behavior; it does not prove production capability isolation, daemon privilege separation, seccomp/capability policy, physical interface ownership, or hardened service design.

## Future privileged implementation requirements

The next product backends must retain structured operations, least privilege, fail-closed validation, atomic or compensating application where physical atomicity is unavailable, observed-state verification, protected recovery, and evidence-backed status. Raw user-controlled shell execution must not become the normal configuration path.

The namespace adapter must not be connected to full transaction apply until each required backend has defined observation and rollback/recovery semantics. Durable production recovery must use an approved protected storage and recovery design, including secret separation and the applicable Everkeep/Privacy Shield contracts, before it can replace the prototype journal.

## Vulnerability reporting

Do not publish exploitable security details, credentials, keys, or protected infrastructure information in public issues. Use the approved GoreeCloud security-reporting path applicable at the time of reporting.
