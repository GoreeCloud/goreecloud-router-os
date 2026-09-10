from __future__ import annotations

from typing import Any, Mapping

from .model import ConfigRevision
from .validator import validate_config


def compile_plan(config: Mapping[str, Any]) -> dict[str, Any]:
    """Compile validated configuration to a deterministic, abstract plan.

    The plan describes intended privileged operations but is deliberately not
    executable by this prototype.
    """
    validate_config(config)
    revision = ConfigRevision.from_config(config)
    by_role = {item["role"]: item for item in revision.normalized["interfaces"]}
    wan = by_role["wan"]
    lan = by_role["lan"]
    return {
        "plan_version": "0.1",
        "revision": revision.digest,
        "operations": [
            {"kind": "interface.configure", "role": "wan", "name": wan["name"], "mode": "dhcp"},
            {"kind": "interface.configure", "role": "lan", "name": lan["name"], "mode": "static", "address": lan["address"]},
            {"kind": "sysctl.intent", "setting": "net.ipv4.ip_forward", "value": 1},
            {"kind": "dhcp.intent", "interface": lan["name"], "scope": lan["dhcp"]},
            {"kind": "firewall.intent", "backend": "nftables", "policy": revision.normalized["firewall"]},
            {"kind": "management.intent", "bind_role": "lan", "authenticated": True},
        ],
    }
