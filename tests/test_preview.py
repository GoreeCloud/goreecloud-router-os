from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from prototype.routeros_m0 import (
    InMemoryRuntime,
    PreviewMismatch,
    apply_reviewed_transaction,
    preview_changes,
    preview_matches,
)

ROOT = Path(__file__).resolve().parents[1]


def reference_config():
    return json.loads((ROOT / "config/examples/reference-build-0.1.json").read_text(encoding="utf-8"))


def alternate_config(subnet_octet: int = 60):
    config = reference_config()
    config["interfaces"][1]["address"] = f"192.168.{subnet_octet}.1/24"
    config["interfaces"][1]["dhcp"]["start"] = f"192.168.{subnet_octet}.100"
    config["interfaces"][1]["dhcp"]["end"] = f"192.168.{subnet_octet}.199"
    return config


class PreviewTests(unittest.TestCase):
    def test_no_change_is_none_risk_and_deterministic(self):
        config = reference_config()
        first = preview_changes(config, config)
        second = preview_changes(deepcopy(config), deepcopy(config))
        self.assertEqual(first, second)
        self.assertEqual(first.risk, "none")
        self.assertFalse(first.requires_connectivity_confirmation)
        self.assertEqual(first.changes, ())

    def test_initial_configuration_requires_confirmation(self):
        report = preview_changes(reference_config(), None)
        self.assertEqual(report.risk, "high")
        self.assertTrue(report.requires_connectivity_confirmation)

    def test_lan_address_change_is_critical_without_exposing_address_value(self):
        previous = reference_config()
        desired = alternate_config(60)
        report = preview_changes(desired, previous)
        self.assertEqual(report.risk, "critical")
        self.assertTrue(report.requires_connectivity_confirmation)
        encoded = repr(report)
        self.assertNotIn("192.168.60.1", encoded)
        self.assertIn("lan.address", [change.field for change in report.changes])

    def test_dhcp_lease_only_is_low_risk(self):
        previous = reference_config()
        desired = deepcopy(previous)
        desired["interfaces"][1]["dhcp"]["lease_seconds"] = 86400
        report = preview_changes(desired, previous)
        self.assertEqual(report.risk, "low")
        self.assertFalse(report.requires_connectivity_confirmation)

    def test_unknown_secret_like_field_is_not_emitted(self):
        previous = reference_config()
        desired = deepcopy(previous)
        desired["management"]["password"] = "do-not-display"
        report = preview_changes(desired, previous)
        self.assertNotIn("do-not-display", repr(report))

    def test_preview_token_changes_when_candidate_changes(self):
        previous = reference_config()
        desired = deepcopy(previous)
        desired["interfaces"][1]["dhcp"]["lease_seconds"] = 86400
        report = preview_changes(desired, previous)
        changed = deepcopy(desired)
        changed["interfaces"][1]["dhcp"]["lease_seconds"] = 7200
        self.assertFalse(preview_matches(report, changed, previous))

    def test_reviewed_apply_succeeds_for_exact_previous_and_desired_pair(self):
        previous = alternate_config(60)
        desired = reference_config()
        runtime = InMemoryRuntime(previous)
        report = preview_changes(desired, previous)
        result = apply_reviewed_transaction(desired, runtime, report)
        self.assertTrue(result.retained)

    def test_reviewed_apply_refuses_stale_previous_state_without_mutation(self):
        reviewed_previous = alternate_config(60)
        actual_previous = alternate_config(70)
        desired = reference_config()
        runtime = InMemoryRuntime(actual_previous)
        report = preview_changes(desired, reviewed_previous)
        before = runtime.snapshot()
        with self.assertRaises(PreviewMismatch):
            apply_reviewed_transaction(desired, runtime, report)
        self.assertEqual(before, runtime.snapshot())

    def test_reviewed_apply_refuses_changed_candidate_without_mutation(self):
        previous = reference_config()
        reviewed_candidate = deepcopy(previous)
        reviewed_candidate["interfaces"][1]["dhcp"]["lease_seconds"] = 86400
        changed_candidate = deepcopy(previous)
        changed_candidate["interfaces"][1]["dhcp"]["lease_seconds"] = 7200
        runtime = InMemoryRuntime(previous)
        report = preview_changes(reviewed_candidate, previous)
        before = runtime.snapshot()
        with self.assertRaises(PreviewMismatch):
            apply_reviewed_transaction(changed_candidate, runtime, report)
        self.assertEqual(before, runtime.snapshot())


if __name__ == "__main__":
    unittest.main()
