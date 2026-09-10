# GoreeCloud Router OS — Security

## Security status

The current repository is a Development / Milestone 0 prototype. It is not a production firewall, security appliance, VPN gateway, or hardened router distribution.

## Current trust boundary

The prototype performs local parsing, validation, hashing, plan generation, and in-memory transaction simulation. It does not execute privileged system commands or modify network state.

## Security invariants enforced now

- Management binding to the WAN role is rejected by the reference profile.
- The current reference profile requires a default-deny firewall intent.
- WAN and LAN interface identities must be distinct.
- Configured IPv4 subnets must not overlap.
- LAN DHCP pools must remain inside the LAN subnet and exclude the router address.
- Transaction verification failure triggers rollback to the previous mock known-good state.

## Future privileged implementation requirements

A future runtime must use structured privileged operations, least privilege, fail-closed validation, atomic or compensating application where physical atomicity is unavailable, observed-state verification, protected recovery, and evidence-backed security status. Raw user-controlled shell execution must not become the normal configuration path.

## Vulnerability reporting

Do not publish exploitable security details, credentials, keys, or protected infrastructure information in public issues. Use the approved GoreeCloud security-reporting path applicable at the time of reporting.
