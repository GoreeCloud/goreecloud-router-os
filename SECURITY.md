# GoreeCloud Router OS — Security

## Security status

The current repository is a Development / Milestone 0 prototype. It is not a production firewall, security appliance, VPN gateway, or hardened router distribution.

## Current trust boundary

The prototype performs local parsing, validation, hashing, plan generation, in-memory transaction simulation, and optional local transaction journaling. It does not execute privileged system commands or modify network state.

The journal is intentionally restricted to the current secret-free prototype configuration. It is not a credential store, Everkeep implementation, or security attestation mechanism.

## Security invariants enforced now

- Management binding to the WAN role is rejected by the reference profile.
- The current reference profile requires a default-deny firewall intent.
- WAN and LAN interface identities must be distinct.
- Configured IPv4 subnets must not overlap.
- LAN DHCP pools must remain inside the LAN subnet and exclude the router address.
- Transaction verification failure triggers rollback to the previous mock known-good state.
- Journal persistence rejects defined sensitive field names and uses restrictive POSIX permissions.
- Journal reads fail closed on malformed content, unexpected fields, digest mismatches, or checksum mismatches.
- Interrupted recovery automatically accepts only exact previous/desired revisions; unknown third states are not overwritten.

The journal checksum is unkeyed and should be understood as corruption/consistency detection, not protection against an attacker who can rewrite both content and checksum.

## Future privileged implementation requirements

A future runtime must use structured privileged operations, least privilege, fail-closed validation, atomic or compensating application where physical atomicity is unavailable, observed-state verification, protected recovery, and evidence-backed security status. Raw user-controlled shell execution must not become the normal configuration path.

Durable production recovery must use an approved protected storage and recovery design, including secret separation and the applicable Everkeep/Privacy Shield contracts, before it can replace this prototype journal.

## Vulnerability reporting

Do not publish exploitable security details, credentials, keys, or protected infrastructure information in public issues. Use the approved GoreeCloud security-reporting path applicable at the time of reporting.
