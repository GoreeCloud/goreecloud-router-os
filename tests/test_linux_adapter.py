from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from lab.privileged_adapter_smoke import supported_adapter_subset
from prototype.routeros_m0 import compile_plan
from prototype.routeros_m0.linux_adapter import (
    AdapterError,
    LinuxNamespaceExecutionAdapter,
    TargetValidationError,
    UnsupportedOperation,
)

ROOT = Path(__file__).resolve().parents[1]


def reference_plan():
    config = json.loads((ROOT / "config/examples/reference-build-0.1.json").read_text(encoding="utf-8"))
    return compile_plan(config)


class FakeRunner:
    def __init__(self):
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, command, *, check=True, text=True, stdout=None, stderr=None):
        argv = tuple(command)
        self.calls.append(argv)
        output = ""
        returncode = 0
        if argv[-2:] == ("netns", "list"):
            output = "gcr-a-12345\n"
        return subprocess.CompletedProcess(list(argv), returncode, stdout=output, stderr="")


class AdapterPreflightTests(unittest.TestCase):
    def setUp(self):
        self.full_plan = reference_plan()
        self.subset = supported_adapter_subset(self.full_plan)
        self.interface = next(
            operation["name"]
            for operation in self.subset["operations"]
            if operation["kind"] == "interface.configure"
        )

    def adapter(self, *, runner=None):
        return LinuxNamespaceExecutionAdapter("gcr-a-12345", [self.interface], runner=runner)

    def test_supported_subset_renders_three_namespace_only_commands(self):
        prepared = self.adapter().preflight(self.subset)
        self.assertEqual(len(prepared.commands), 3)
        self.assertEqual(prepared.required_interfaces, (self.interface,))
        for command in prepared.commands:
            self.assertEqual(command.argv[0], "ip")
            self.assertIn("gcr-a-12345", command.argv)
            self.assertNotIn(command.argv[0], {"bash", "sh", "zsh", "fish", "powershell", "pwsh"})

    def test_full_reference_plan_is_refused_before_any_runner_call(self):
        runner = FakeRunner()
        adapter = self.adapter(runner=runner)
        with self.assertRaises(UnsupportedOperation):
            adapter.execute(self.full_plan)
        self.assertEqual(runner.calls, [])

    def test_namespace_must_be_generated_gcr_namespace(self):
        for name in ("root", "router", "default", "gcr_A", "gcr-"):
            with self.subTest(name=name):
                with self.assertRaises(TargetValidationError):
                    LinuxNamespaceExecutionAdapter(name, [self.interface])

    def test_interface_must_be_safe_and_allowlisted(self):
        with self.assertRaises(TargetValidationError):
            LinuxNamespaceExecutionAdapter("gcr-a-12345", ["lan0;rm"])
        adapter = LinuxNamespaceExecutionAdapter("gcr-a-12345", ["approved0"])
        with self.assertRaises(TargetValidationError):
            adapter.preflight(self.subset)

    def test_dhcp_interface_mode_is_not_supported(self):
        plan = deepcopy(self.subset)
        operation = next(item for item in plan["operations"] if item["kind"] == "interface.configure")
        operation["mode"] = "dhcp"
        with self.assertRaises(UnsupportedOperation):
            self.adapter().preflight(plan)

    def test_unimplemented_backend_kinds_fail_closed(self):
        for kind in ("dhcp.intent", "firewall.intent", "management.intent"):
            with self.subTest(kind=kind):
                plan = {
                    "plan_version": "0.1",
                    "revision": "a" * 64,
                    "operations": [{"kind": kind}],
                }
                with self.assertRaises(UnsupportedOperation):
                    self.adapter().preflight(plan)

    def test_only_ipv4_forwarding_sysctl_with_integer_boolean_value_is_accepted(self):
        for setting, value in (
            ("kernel.hostname", 1),
            ("net.ipv4.ip_forward", 2),
            ("net.ipv4.ip_forward", True),
        ):
            with self.subTest(setting=setting, value=value):
                plan = {
                    "plan_version": "0.1",
                    "revision": "a" * 64,
                    "operations": [{"kind": "sysctl.intent", "setting": setting, "value": value}],
                }
                with self.assertRaises(UnsupportedOperation):
                    self.adapter().preflight(plan)

        for value in (0, 1):
            plan = {
                "plan_version": "0.1",
                "revision": "a" * 64,
                "operations": [{"kind": "sysctl.intent", "setting": "net.ipv4.ip_forward", "value": value}],
            }
            prepared = self.adapter().preflight(plan)
            self.assertEqual(len(prepared.commands), 1)

    def test_revision_must_be_exact_lowercase_sha256(self):
        for revision in ("a" * 63, "A" * 64, "g" * 64, "sha256:" + "a" * 64, None):
            with self.subTest(revision=revision):
                plan = deepcopy(self.subset)
                plan["revision"] = revision
                with self.assertRaises(AdapterError):
                    self.adapter().preflight(plan)


class AdapterExecutionTests(unittest.TestCase):
    def setUp(self):
        self.plan = supported_adapter_subset(reference_plan())
        self.interface = next(
            operation["name"]
            for operation in self.plan["operations"]
            if operation["kind"] == "interface.configure"
        )

    def test_execute_probes_target_then_uses_absolute_tool_paths(self):
        runner = FakeRunner()
        adapter = LinuxNamespaceExecutionAdapter("gcr-a-12345", [self.interface], runner=runner)

        def fake_which(tool):
            return f"/usr/sbin/{tool}"

        with patch("prototype.routeros_m0.linux_adapter.os.geteuid", return_value=0), patch(
            "prototype.routeros_m0.linux_adapter.shutil.which", side_effect=fake_which
        ):
            result = adapter.execute(self.plan)

        self.assertEqual(result.commands_executed, 3)
        self.assertEqual(runner.calls[0], ("/usr/sbin/ip", "netns", "list"))
        self.assertEqual(
            runner.calls[1],
            ("/usr/sbin/ip", "-n", "gcr-a-12345", "link", "show", "dev", self.interface),
        )
        for command in runner.calls[2:]:
            self.assertEqual(command[0], "/usr/sbin/ip")
            self.assertNotIn("bash", command)
            self.assertNotIn("sh", command)
        sysctl_command = next(command for command in runner.calls if "-w" in command)
        self.assertEqual(sysctl_command[4], "/usr/sbin/sysctl")

    def test_non_root_execution_fails_before_target_probe(self):
        runner = FakeRunner()
        adapter = LinuxNamespaceExecutionAdapter("gcr-a-12345", [self.interface], runner=runner)
        with patch("prototype.routeros_m0.linux_adapter.os.geteuid", return_value=1000):
            with self.assertRaises(TargetValidationError):
                adapter.execute(self.plan)
        self.assertEqual(runner.calls, [])


if __name__ == "__main__":
    unittest.main()
