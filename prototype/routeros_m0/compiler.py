from __future__ import annotations

from ipaddress import ip_interface
from typing import Any, Mapping

from .model import ConfigRevision
from .validator import validate_config


def compile_plan(config: Mapping[str, Any]) -> dict[str, Any]:
    validate_config(config)
    revision = ConfigRevision.from_config(config)
    by_role = {item["role"]: item for item in revision.normalized["interfaces"]}
    wan = by_role["wan"]
    lan = by_role["lan"]
    lan_subnet = str(ip_interface(lan["address"]).network)
    return {
        "plan_version": "0.1",
        "revision": revision.digest,
        "operations": [
            {"kind": "interface.configure", "role": "wan", "name": wan["name"], "mode": "dhcp"},
            {"kind": "interface.configure", "role": "lan", "name": lan["name"], "mode": "static", "address": lan["address"]},
            {"kind": "sysctl.intent", "setting": "net.ipv4.ip_forward", "value": 1},
            {"kind": "dhcp.intent", "interface": lan["name"], "scope": lan["dhcp"]},
            {
                "kind": "firewall.intent",
                "backend": "nftables",
                "policy": revision.normalized["firewall"],
                "lan_interface": lan["name"],
                "wan_interface": wan["name"],
                "lan_subnet": lan_subnet,
                "ipv4_masquerade": True,
            },
            {"kind": "management.intent", "bind_role": "lan", "authenticated": True},
        ],
    }
