from __future__ import annotations

import unittest

from lab.reference_build_0_1 import LabNames, planned_operations


class VirtualLabPlanTests(unittest.TestCase):
    def setUp(self):
        self.names = LabNames.for_pid(12345)
        self.commands = planned_operations(self.names)

    def test_namespace_and_interface_names_are_bounded(self):
        self.assertTrue(self.names.router.startswith("gcr-r-"))
        for interface in (
            self.names.wan_router_if,
            self.names.wan_peer_if,
            self.names.lan_router_if,
            self.names.lan_peer_if,
        ):
            self.assertLessEqual(len(interface.encode("utf-8")), 15)

    def test_plan_has_no_shell_or_arbitrary_interpreter(self):
        forbidden = {"bash", "sh", "zsh", "fish", "powershell", "pwsh"}
        for command in self.commands:
            self.assertNotIn(command[0], forbidden)
            self.assertNotIn("-c", command[:2])

    def test_host_default_route_is_never_modified(self):
        for command in self.commands:
            if command[:2] == ("ip", "route"):
                self.fail(f"host route command is forbidden: {command}")
            if "route" in command:
                self.assertIn("-n", command, f"route operation must target a namespace: {command}")

    def test_sysctl_is_scoped_to_router_namespace(self):
        sysctl_commands = [command for command in self.commands if "sysctl" in command]
        self.assertEqual(len(sysctl_commands), 1)
        command = sysctl_commands[0]
        self.assertEqual(command[:4], ("ip", "netns", "exec", self.names.router))
        self.assertEqual(command[-1], "net.ipv4.ip_forward=1")

    def test_plan_uses_documentation_only_wan_range(self):
        flattened = " ".join(part for command in self.commands for part in command)
        self.assertIn("198.51.100.1/30", flattened)
        self.assertIn("198.51.100.2/30", flattened)

    def test_plan_contains_three_namespaces_and_two_veth_pairs(self):
        additions = [command for command in self.commands if command[:3] == ("ip", "netns", "add")]
        veths = [command for command in self.commands if command[:3] == ("ip", "link", "add")]
        self.assertEqual(len(additions), 3)
        self.assertEqual(len(veths), 2)


if __name__ == "__main__":
    unittest.main()
