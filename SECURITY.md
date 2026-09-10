# GoreeCloud Router OS — Security

## Security status

The current repository is a Development / Milestone 0 prototype. It is not a production firewall, security appliance, VPN gateway, or hardened router distribution.

## Current trust boundary

The **product prototype** performs local parsing, validation, hashing, abstract plan generation, privacy-safe preview/review checks, in-memory transaction simulation, and optional local transaction journaling. Product-prototype code does not execute privileged system commands or modify network state.

A separate **development-only virtual network lab** uses privileged Linux namespace operations on an ephemeral CI runner. The lab creates only generated network namespaces and veth pairs, applies addresses/routes inside those namespaces, enables IPv4 forwarding only inside the router namespace, performs a routed ping smoke test, and tears the namespaces down. This privilege must not be treated as a Router OS runtime privilege boundary or as evidence that a production privileged execution adapter exists.

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
- Virtual-lab route modifications must target named namespaces; host-route commands are rejected by plan tests.
- The virtual lab snapshots the host default route and fails if it changes during the run.
- Virtual-lab teardown verifies that generated namespaces are removed.

The journal checksum is unkeyed and should be understood as corruption/consistency detection, not protection against an attacker who can rewrite both content and checksum.

## Virtual lab boundary

The namespace lab is intentionally a test harness. It does not execute a Router OS nftables policy, NAT backend, DHCP backend, management API, Wi-Fi control path, VPN path, or platform integration. Its temporary WAN address is fixed test plumbing and does not satisfy the Reference Build 0.1 DHCP-WAN requirement.

The CI workflow grants elevated privileges only to the reviewed lab script on the disposable hosted runner. The workflow retains `contents: read` permissions and does not require repository secrets for the lab.

## Future privileged implementation requirements

A future Router OS runtime must use structured privileged operations, least privilege, fail-closed validation, atomic or compensating application where physical atomicity is unavailable, observed-state verification, protected recovery, and evidence-backed security status. Raw user-controlled shell execution must not become the normal configuration path.

Durable production recovery must use an approved protected storage and recovery design, including secret separation and the applicable Everkeep/Privacy Shield contracts, before it can replace this prototype journal.

## Vulnerability reporting

Do not publish exploitable security details, credentials, keys, or protected infrastructure information in public issues. Use the approved GoreeCloud security-reporting path applicable at the time of reporting.
