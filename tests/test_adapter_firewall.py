from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from prototype.routeros_m0.compiler import compile_plan
from prototype.routeros_m0.linux_adapter import LinuxNamespaceExecutionAdapter, UnsupportedOperation

ROOT = Path(__file__).resolve().parents[1]


def plan():
    config = json.loads((ROOT / "config/examples/reference-build-0.1.json").read_text())
    return compile_plan(config)


def firewall_subset(full):
    kinds = {"interface.configure", "sysctl.intent", "firewall.intent"}
    operations = [
        item for item in full["operations"]
        if item["kind"] in kinds and not (item["kind"] == "interface.configure" and item["role"] == "wan")
    ]
    return {"plan_version": full["plan_version"], "revision": full["revision"], "operations": operations}


class Runner:
    def __init__(self):
        self.calls = []
        self.inputs = []
        self.checks = []

    def __call__(self, command, *, check=True, text=True, stdout=None, stderr=None, input=None):
        argv = tuple(command)
        self.calls.append(argv)
        self.inputs.append(input)
        self.checks.append(check)
        output = "gcr-a-12345\n" if argv[-2:] == ("netns", "list") else ""
        return subprocess.CompletedProcess(list(argv), 0, stdout=output, stderr="")


class FirewallAdapterTests(unittest.TestCase):
    def test_firewall_subset_renders_staged_check_and_atomic_apply(self):
        full = plan()
        subset = firewall_subset(full)
        adapter = LinuxNamespaceExecutionAdapter("gcr-a-12345", ["lan0", "wan0"])
        prepared = adapter.preflight(subset)
        self.assertEqual(prepared.required_interfaces, ("lan0", "wan0"))
        kinds = [item.kind for item in prepared.commands]
        self.assertEqual(kinds[-4:], [
            "nftables.stage.filter_table",
            "nftables.stage.nat_table",
            "nftables.check",
            "nftables.apply",
        ])
        self.assertFalse(prepared.commands[-4].check)
        self.assertFalse(prepared.commands[-3].check)
        self.assertIn("flush table inet goreecloud_filter", prepared.commands[-2].stdin)
        self.assertEqual(prepared.commands[-2].stdin, prepared.commands[-1].stdin)

    def test_full_reference_plan_still_fails_closed_before_execution(self):
        runner = Runner()
        adapter = LinuxNamespaceExecutionAdapter("gcr-a-12345", ["lan0", "wan0"], runner=runner)
        with self.assertRaises(UnsupportedOperation):
            adapter.execute(plan())
        self.assertEqual(runner.calls, [])

    def test_execution_materializes_nft_and_passes_ruleset_only_on_nft_batch_commands(self):
        runner = Runner()
        subset = firewall_subset(plan())
        adapter = LinuxNamespaceExecutionAdapter("gcr-a-12345", ["lan0", "wan0"], runner=runner)
        with patch("prototype.routeros_m0.linux_adapter.os.geteuid", return_value=0), patch(
            "prototype.routeros_m0.linux_adapter.shutil.which", side_effect=lambda tool: f"/usr/sbin/{tool}"
        ):
            result = adapter.execute(subset)
        self.assertEqual(result.commands_executed, 7)
        nft_calls = [
            (call, payload, check)
            for call, payload, check in zip(runner.calls, runner.inputs, runner.checks)
            if "/usr/sbin/nft" in call
        ]
        self.assertEqual(len(nft_calls), 4)
        self.assertIsNone(nft_calls[0][1])
        self.assertFalse(nft_calls[0][2])
        self.assertIsNone(nft_calls[1][1])
        self.assertFalse(nft_calls[1][2])
        self.assertIsNotNone(nft_calls[2][1])
        self.assertTrue(nft_calls[2][2])
        self.assertEqual(nft_calls[2][1], nft_calls[3][1])
        self.assertTrue(nft_calls[2][0][-3:] == ("--check", "-f", "-"))
        self.assertTrue(nft_calls[3][0][-2:] == ("-f", "-"))


if __name__ == "__main__":
    unittest.main()
