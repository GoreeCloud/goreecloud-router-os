from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from prototype.routeros_m0 import (
    ConfigRevision,
    InMemoryRuntime,
    ValidationError,
    apply_transaction,
    compile_plan,
    validate_config,
)

ROOT = Path(__file__).resolve().parents[1]


def reference_config():
    return json.loads((ROOT / "config/examples/reference-build-0.1.json").read_text(encoding="utf-8"))


class ValidationTests(unittest.TestCase):
    def test_reference_config_is_valid(self):
        validate_config(reference_config())

    def test_duplicate_interface_names_fail(self):
        config = reference_config()
        config["interfaces"][1]["name"] = config["interfaces"][0]["name"]
        with self.assertRaises(ValidationError):
            validate_config(config)

    def test_management_on_wan_fails(self):
        config = reference_config()
        config["management"]["bind_role"] = "wan"
        with self.assertRaises(ValidationError):
            validate_config(config)

    def test_dhcp_pool_outside_lan_fails(self):
        config = reference_config()
        config["interfaces"][1]["dhcp"]["start"] = "192.168.51.100"
        with self.assertRaises(ValidationError):
            validate_config(config)

    def test_dhcp_pool_must_exclude_router_address(self):
        config = reference_config()
        config["interfaces"][1]["dhcp"]["start"] = "192.168.50.1"
        with self.assertRaises(ValidationError):
            validate_config(config)

    def test_default_forward_must_drop(self):
        config = reference_config()
        config["firewall"]["default_forward"] = "accept"
        with self.assertRaises(ValidationError):
            validate_config(config)


class DeterminismTests(unittest.TestCase):
    def test_revision_digest_ignores_key_order(self):
        config = reference_config()
        reordered = {key: config[key] for key in reversed(list(config.keys()))}
        self.assertEqual(ConfigRevision.from_config(config).digest, ConfigRevision.from_config(reordered).digest)

    def test_plan_is_deterministic(self):
        config = reference_config()
        self.assertEqual(compile_plan(config), compile_plan(deepcopy(config)))

    def test_plan_contains_no_executable_command_field(self):
        encoded = json.dumps(compile_plan(reference_config()))
        self.assertNotIn('"command"', encoded)
        self.assertNotIn('"shell"', encoded)


class TransactionTests(unittest.TestCase):
    def test_successful_apply_is_retained_after_verification(self):
        config = reference_config()
        runtime = InMemoryRuntime()
        result = apply_transaction(config, runtime)
        self.assertTrue(result.retained)
        self.assertFalse(result.rolled_back)
        self.assertEqual(result.desired_revision, result.applied_revision)
        self.assertEqual(result.desired_revision, result.observed_revision)

    def test_failed_verification_rolls_back_to_previous_known_good(self):
        previous = reference_config()
        previous["interfaces"][1]["address"] = "192.168.60.1/24"
        previous["interfaces"][1]["dhcp"]["start"] = "192.168.60.100"
        previous["interfaces"][1]["dhcp"]["end"] = "192.168.60.199"
        validate_config(previous)

        runtime = InMemoryRuntime(previous)
        runtime.force_verification_failure = True
        candidate = reference_config()
        result = apply_transaction(candidate, runtime)

        self.assertTrue(result.rolled_back)
        self.assertFalse(result.retained)
        self.assertEqual(ConfigRevision.from_config(previous).digest, ConfigRevision.from_config(runtime.snapshot()).digest)

    def test_candidate_does_not_mutate_runtime_before_apply(self):
        previous = reference_config()
        runtime = InMemoryRuntime(previous)
        candidate = reference_config()
        candidate["interfaces"][1]["address"] = "192.168.70.1/24"
        candidate["interfaces"][1]["dhcp"]["start"] = "192.168.70.100"
        candidate["interfaces"][1]["dhcp"]["end"] = "192.168.70.199"
        validate_config(candidate)
        self.assertEqual(ConfigRevision.from_config(previous).digest, ConfigRevision.from_config(runtime.snapshot()).digest)


if __name__ == "__main__":
    unittest.main()
