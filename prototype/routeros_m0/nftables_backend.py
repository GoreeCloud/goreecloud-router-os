from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_network
import re
from typing import Any, Mapping


class NftablesBackendError(ValueError):
    """Raised when a firewall intent cannot be compiled by the bounded backend."""


_INTERFACE_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_REQUIRED_POLICY = {
    "default_input": "drop",
    "default_forward": "drop",
    "allow_established": True,
    "allow_lan_to_wan": True,
}
FILTER_TABLE = "goreecloud_filter"
NAT_TABLE = "goreecloud_nat"


def _interface_name(value: Any) -> str:
    if not isinstance(value, str) or not value or not _INTERFACE_RE.fullmatch(value):
        raise NftablesBackendError("firewall interface name contains unsupported characters")
    if len(value.encode("utf-8")) > 15:
        raise NftablesBackendError("firewall interface name exceeds the Linux interface-name limit")
    return value


def _lan_subnet(value: Any) -> str:
    if not isinstance(value, str):
        raise NftablesBackendError("firewall LAN subnet must be a string")
    try:
        network = ip_network(value, strict=True)
    except ValueError as exc:
        raise NftablesBackendError("firewall LAN subnet is invalid") from exc
    if network.version != 4:
        raise NftablesBackendError("Reference Build 0.1 firewall accepts IPv4 LAN subnets only")
    return str(network)


@dataclass(frozen=True)
class NftablesRuleset:
    lan_interface: str
    wan_interface: str
    lan_subnet: str
    script: str


def compile_firewall_intent(operation: Mapping[str, Any]) -> NftablesRuleset:
    """Compile the exact Reference Build 0.1 firewall intent to dedicated nftables tables.

    This compiler intentionally supports only the already-validated Reference Build 0.1
    policy. Unknown fields fail closed so future policy extensions cannot be silently
    ignored by an older privileged backend.
    """
    if not isinstance(operation, Mapping) or operation.get("kind") != "firewall.intent":
        raise NftablesBackendError("expected a firewall.intent operation")
    if operation.get("backend") != "nftables":
        raise NftablesBackendError("Reference Build 0.1 requires the nftables backend")

    policy = operation.get("policy")
    if not isinstance(policy, Mapping):
        raise NftablesBackendError("firewall policy must be a mapping")
    if set(policy) != set(_REQUIRED_POLICY):
        raise NftablesBackendError("firewall policy contains missing or unsupported fields")
    if dict(policy) != _REQUIRED_POLICY:
        raise NftablesBackendError("firewall policy does not match the accepted Reference Build 0.1 policy")

    lan = _interface_name(operation.get("lan_interface"))
    wan = _interface_name(operation.get("wan_interface"))
    if lan == wan:
        raise NftablesBackendError("LAN and WAN firewall interfaces must be distinct")
    subnet = _lan_subnet(operation.get("lan_subnet"))
    if operation.get("ipv4_masquerade") is not True:
        raise NftablesBackendError("Reference Build 0.1 requires IPv4 masquerade")

    script = "\n".join(
        (
            f"flush table inet {FILTER_TABLE}",
            f"add chain inet {FILTER_TABLE} input {{ type filter hook input priority 0; policy drop; }}",
            f"add chain inet {FILTER_TABLE} forward {{ type filter hook forward priority 0; policy drop; }}",
            f"add rule inet {FILTER_TABLE} input ct state established,related accept",
            f"add rule inet {FILTER_TABLE} forward ct state established,related accept",
            f'add rule inet {FILTER_TABLE} forward iifname "{lan}" oifname "{wan}" ip saddr {subnet} accept',
            f"flush table ip {NAT_TABLE}",
            f"add chain ip {NAT_TABLE} postrouting {{ type nat hook postrouting priority srcnat; policy accept; }}",
            f'add rule ip {NAT_TABLE} postrouting oifname "{wan}" ip saddr {subnet} masquerade',
            "",
        )
    )
    return NftablesRuleset(lan_interface=lan, wan_interface=wan, lan_subnet=subnet, script=script)
