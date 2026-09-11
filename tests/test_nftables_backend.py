from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from prototype.routeros_m0.compiler import compile_plan
from prototype.routeros_m0.nftables_backend import (
    FILTER_TABLE,
    NAT_TABLE,
    NftablesBackendError,
    compile_firewall_intent,
)

ROOT = Path(__file__).resolve().parents[1]


def firewall_operation():
    config = json.loads((ROOT / "config/examples/reference-build-0.1.json").read_text())
    plan = compile_plan(config)
    return next(item for item in plan["operations"] if item["kind"] == "firewall.intent")


class NftablesBackendTests(unittest.TestCase):
    def test_compiler_carries_explicit_firewall_context(self):
        operation = firewall_operation()
        self.assertEqual(operation["lan_interface"], "lan0")
        self.assertEqual(operation["wan_interface"], "wan0")
        self.assertEqual(operation["lan_subnet"], "192.168.50.0/24")
        self.assertIs(operation["ipv4_masquerade"], True)

    def test_ruleset_is_deterministic_and_dedicated(self):
        first = compile_firewall_intent(firewall_operation())
        second = compile_firewall_intent(firewall_operation())
        self.assertEqual(first, second)
        self.assertIn(f"flush table inet {FILTER_TABLE}", first.script)
        self.assertIn(f"flush table ip {NAT_TABLE}", first.script)
        self.assertIn("ct state established,related accept", first.script)
        self.assertIn('iifname "lan0" oifname "wan0" ip saddr 192.168.50.0/24 accept', first.script)
        self.assertIn('oifname "wan0" ip saddr 192.168.50.0/24 masquerade', first.script)
        self.assertNotIn("flush ruleset", first.script)
        self.assertNotIn("shell", first.script.lower())

    def test_unknown_or_changed_policy_fails_closed(self):
        for change in ("extra", "wrong-value"):
            operation = deepcopy(firewall_operation())
            if change == "extra":
                operation["policy"]["future_policy"] = True
            else:
                operation["policy"]["allow_lan_to_wan"] = False
            with self.subTest(change=change):
                with self.assertRaises(NftablesBackendError):
                    compile_firewall_intent(operation)

    def test_backend_target_and_nat_intent_fail_closed(self):
        for field, value in (("backend", "iptables"), ("ipv4_masquerade", False)):
            operation = deepcopy(firewall_operation())
            operation[field] = value
            with self.subTest(field=field):
                with self.assertRaises(NftablesBackendError):
                    compile_firewall_intent(operation)

    def test_interfaces_and_subnet_are_strictly_validated(self):
        cases = [
            ("lan_interface", "lan0;touch"),
            ("wan_interface", "x" * 16),
            ("wan_interface", "lan0"),
            ("lan_subnet", "192.168.50.1/24"),
            ("lan_subnet", "2001:db8::/64"),
        ]
        for field, value in cases:
            operation = deepcopy(firewall_operation())
            operation[field] = value
            with self.subTest(field=field, value=value):
                with self.assertRaises(NftablesBackendError):
                    compile_firewall_intent(operation)


if __name__ == "__main__":
    unittest.main()
