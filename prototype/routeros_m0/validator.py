from __future__ import annotations

from ipaddress import ip_address, ip_interface
from typing import Any, Mapping


class ValidationError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def validate_config(config: Mapping[str, Any]) -> None:
    """Validate the current narrow Reference Build 0.1 profile.

    This is intentionally stricter than a future general Router OS schema.
    It validates the two-interface development target and performs no host I/O.
    """
    _require(config.get("schema_version") == "0.1", "schema_version must be 0.1")
    _require(config.get("profile") == "reference-build-0.1", "unsupported profile")

    interfaces = config.get("interfaces")
    _require(isinstance(interfaces, list) and len(interfaces) == 2, "reference build requires exactly two interfaces")

    names = [i.get("name") for i in interfaces if isinstance(i, Mapping)]
    _require(len(names) == 2 and all(isinstance(n, str) and n for n in names), "each interface requires a non-empty name")
    _require(len(set(names)) == 2, "interface names must be unique")

    by_role = {i.get("role"): i for i in interfaces if isinstance(i, Mapping)}
    _require(set(by_role) == {"wan", "lan"}, "exactly one wan and one lan interface are required")

    wan = by_role["wan"]
    lan = by_role["lan"]
    _require(wan.get("mode") == "dhcp", "reference-build wan must use DHCP")
    _require(wan.get("address") in (None, ""), "DHCP wan must not define a static address")
    _require(lan.get("mode") == "static", "reference-build lan must use a static address")
    _require(isinstance(lan.get("address"), str), "static lan requires an IPv4 interface address")

    lan_iface = ip_interface(lan["address"])
    _require(lan_iface.version == 4, "reference build currently supports IPv4 LAN addressing only")
    lan_net = lan_iface.network

    # If any other static address appears in future profile extensions, overlap must fail closed.
    static_nets = []
    for item in interfaces:
        address = item.get("address")
        if address:
            iface = ip_interface(address)
            static_nets.append((item.get("role"), iface.network))
    for index, (role_a, net_a) in enumerate(static_nets):
        for role_b, net_b in static_nets[index + 1:]:
            _require(not net_a.overlaps(net_b), f"overlapping interface networks: {role_a} {net_a} and {role_b} {net_b}")

    dhcp = lan.get("dhcp")
    _require(isinstance(dhcp, Mapping), "lan DHCP scope is required")
    start = ip_address(dhcp.get("start"))
    end = ip_address(dhcp.get("end"))
    _require(start.version == end.version == 4, "LAN DHCP pool must be IPv4")
    _require(start in lan_net and end in lan_net, "LAN DHCP pool must be contained in the LAN subnet")
    _require(int(start) <= int(end), "LAN DHCP pool start must not exceed end")
    _require(start != lan_iface.ip and end != lan_iface.ip, "LAN DHCP pool endpoints must not equal the router address")
    _require(not (int(start) <= int(lan_iface.ip) <= int(end)), "LAN DHCP pool must exclude the router address")
    lease = dhcp.get("lease_seconds")
    _require(isinstance(lease, int) and 60 <= lease <= 604800, "lease_seconds must be between 60 and 604800")

    _require(config.get("ipv4_forwarding") is True, "reference build requires IPv4 forwarding intent")

    firewall = config.get("firewall")
    _require(isinstance(firewall, Mapping), "firewall configuration is required")
    _require(firewall.get("default_input") == "drop", "reference build requires default-drop input policy")
    _require(firewall.get("default_forward") == "drop", "reference build requires default-drop forward policy")
    _require(firewall.get("allow_established") is True, "reference build requires established/related state allowance")
    _require(firewall.get("allow_lan_to_wan") is True, "reference build requires explicit LAN-to-WAN allowance")

    management = config.get("management")
    _require(isinstance(management, Mapping), "management configuration is required")
    _require(management.get("bind_role") == "lan", "management must bind to LAN, never WAN, in reference build")
    _require(management.get("authenticated") is True, "management must require authentication")
