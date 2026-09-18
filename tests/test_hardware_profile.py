from __future__ import annotations

import json
from pathlib import Path
import unittest

from prototype.routeros_m0.hardware_profile import (
    HardwareProfileError,
    assess_hardware_readiness,
    load_hardware_profile,
    validate_hardware_profile,
)

ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "hardware/profiles/glinet-gl-mt5000.json"


class Brume3HardwareProfileTests(unittest.TestCase):
    def profile(self):
        return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))

    def test_profile_loads_but_remains_non_installable(self):
        profile = load_hardware_profile(PROFILE_PATH)
        self.assertEqual(profile["profile_id"], "glinet-gl-mt5000")
        self.assertEqual(profile["architecture"], "aarch64")
        self.assertFalse(profile["lifecycle"]["installable"])
        self.assertFalse(profile["lifecycle"]["supported"])
        self.assertFalse(profile["lifecycle"]["hardware_verified"])

    def test_vendor_reported_resource_floor_is_recorded(self):
        profile = load_hardware_profile(PROFILE_PATH)
        self.assertEqual(profile["resources"]["cpu"]["cores"], 4)
        self.assertEqual(profile["resources"]["cpu"]["max_frequency_mhz"], 2000)
        self.assertEqual(profile["resources"]["memory_vendor_capacity"], "1 GB")
        self.assertEqual(profile["storage"]["vendor_capacity"], "8 GB")
        self.assertEqual(len(profile["ethernet"]["ports"]), 3)
        self.assertTrue(
            all(
                port["max_speed_mbps"] == 2500
                for port in profile["ethernet"]["ports"]
            )
        )

    def test_readiness_fails_closed_on_unverified_board_bindings(self):
        readiness = assess_hardware_readiness(
            load_hardware_profile(PROFILE_PATH)
        )
        self.assertFalse(readiness.installable)
        self.assertGreaterEqual(len(readiness.blockers), 10)
        joined = "\n".join(readiness.blockers)
        self.assertIn("Linux interface binding is unknown", joined)
        self.assertIn("eMMC partition map has not been verified", joined)
        self.assertIn("recovery path has not been verified", joined)
        self.assertIn(
            "hardware profile still contains unresolved unknowns",
            joined,
        )

    def test_installable_cannot_be_asserted_without_direct_hardware_verification(self):
        profile = self.profile()
        profile["lifecycle"]["installable"] = True
        with self.assertRaises(HardwareProfileError):
            validate_hardware_profile(profile)

    def test_supported_cannot_be_asserted_from_development_state(self):
        profile = self.profile()
        profile["lifecycle"]["supported"] = True
        with self.assertRaises(HardwareProfileError):
            validate_hardware_profile(profile)

    def test_duplicate_port_labels_are_rejected(self):
        profile = self.profile()
        profile["ethernet"]["ports"][1]["label"] = (
            profile["ethernet"]["ports"][0]["label"]
        )
        with self.assertRaises(HardwareProfileError):
            validate_hardware_profile(profile)

    def test_unknown_architecture_is_rejected(self):
        profile = self.profile()
        profile["architecture"] = "arm"
        with self.assertRaises(HardwareProfileError):
            validate_hardware_profile(profile)

    def test_fully_verified_profile_can_be_assessed_installable(self):
        profile = self.profile()
        profile["lifecycle"].update(
            status="supported",
            installable=True,
            supported=True,
            hardware_verified=True,
        )
        for index, port in enumerate(profile["ethernet"]["ports"]):
            port["kernel_name"] = f"eth{index}"
            port["observed_on_target"] = True
        profile["storage"]["partition_map_verified"] = True
        for field in (
            "boot_chain_verified",
            "recovery_path_verified",
            "device_tree_verified",
            "kernel_support_verified",
            "watchdog_verified",
            "thermal_monitoring_verified",
        ):
            profile["platform"][field] = True
        profile["unknowns"] = []
        validated = validate_hardware_profile(profile)
        readiness = assess_hardware_readiness(validated)
        self.assertTrue(readiness.installable)
        self.assertEqual(readiness.blockers, ())


if __name__ == "__main__":
    unittest.main()
