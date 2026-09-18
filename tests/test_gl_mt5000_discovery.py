from __future__ import annotations

from pathlib import Path
import stat
import subprocess
import tempfile
import unittest

from prototype.routeros_m0.hardware_discovery import (
    DiscoveryReportError,
    parse_discovery_report,
    report_has_hardware_identity,
)

ROOT = Path(__file__).resolve().parents[1]
COLLECTOR = ROOT / "scripts/collect_gl_mt5000_hardware.sh"


def write(root: Path, relative: str, content: str | bytes) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


class GLMT5000DiscoveryTests(unittest.TestCase):
    def fixture_root(self, root: Path) -> None:
        write(root, "tmp/sysinfo/model", "GL.iNet GL-MT5000\n")
        write(root, "tmp/sysinfo/board_name", "glinet,gl-mt5000\n")
        write(
            root,
            "etc/openwrt_release",
            "DISTRIB_ID='OpenWrt'\nDISTRIB_RELEASE='21.02'\n",
        )
        write(
            root,
            "proc/cpuinfo",
            "processor\t: 0\n"
            "model name\t: ARMv8 Processor rev 4 (v8l)\n"
            "CPU architecture: 8\n"
            "Hardware\t: MediaTek test fixture\n"
            "Serial\t\t: 0123456789abcdef\n",
        )
        write(
            root,
            "proc/mtd",
            'dev: size erasesize name\nmtd0: 00100000 00020000 "boot"\n',
        )
        write(
            root,
            "proc/partitions",
            "major minor  #blocks  name\n 179 0 7634944 mmcblk0\n",
        )
        write(
            root,
            "sys/firmware/devicetree/base/model",
            b"GL.iNet GL-MT5000\x00",
        )
        write(
            root,
            "sys/firmware/devicetree/base/compatible",
            b"glinet,gl-mt5000\x00mediatek,test-soc\x00",
        )
        (root / "sys/firmware/devicetree/base/soc/ethernet@15100000").mkdir(
            parents=True,
            exist_ok=True,
        )

        net = root / "sys/class/net/eth0"
        net.mkdir(parents=True, exist_ok=True)
        write(root, "sys/class/net/eth0/ifindex", "2\n")
        write(root, "sys/class/net/eth0/type", "1\n")
        write(root, "sys/class/net/eth0/operstate", "up\n")
        write(root, "sys/class/net/eth0/carrier", "1\n")
        write(root, "sys/class/net/eth0/speed", "2500\n")
        write(root, "sys/class/net/eth0/duplex", "full\n")
        write(root, "sys/class/net/eth0/address", "aa:bb:cc:dd:ee:ff\n")

        block = root / "sys/class/block/mmcblk0"
        block.mkdir(parents=True, exist_ok=True)
        write(root, "sys/class/block/mmcblk0/dev", "179:0\n")
        write(root, "sys/class/block/mmcblk0/size", "15269888\n")
        write(root, "sys/class/block/mmcblk0/ro", "0\n")
        write(root, "sys/class/block/mmcblk0/removable", "0\n")

        wd = root / "sys/class/watchdog/watchdog0"
        wd.mkdir(parents=True, exist_ok=True)
        write(root, "sys/class/watchdog/watchdog0/identity", "fixture-watchdog\n")

        zone = root / "sys/class/thermal/thermal_zone0"
        zone.mkdir(parents=True, exist_ok=True)
        write(root, "sys/class/thermal/thermal_zone0/type", "soc\n")
        write(root, "sys/class/thermal/thermal_zone0/temp", "42000\n")

        write(root, "proc/modules", "mtk_eth 12345 0 - Live 0x00000000\n")

    def run_collector(self, root: Path) -> str:
        result = subprocess.run(
            ["sh", str(COLLECTOR), "--root", str(root)],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return result.stdout

    def test_fixture_report_is_parseable_and_identified(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp)
            self.fixture_root(fixture)
            report = parse_discovery_report(self.run_collector(fixture))
        self.assertEqual(report.profile_id, "glinet-gl-mt5000")
        self.assertTrue(report_has_hardware_identity(report))
        self.assertIn("network.interfaces", report.sections)
        self.assertIn("storage.sysfs", report.sections)

    def test_cpu_serial_and_mac_address_are_not_collected(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp)
            self.fixture_root(fixture)
            text = self.run_collector(fixture)
        self.assertNotIn("0123456789abcdef", text)
        self.assertNotIn("aa:bb:cc:dd:ee:ff", text)
        self.assertNotIn("Serial", text)

    def test_report_records_non_mutating_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp)
            self.fixture_root(fixture)
            text = self.run_collector(fixture)
        for assertion in (
            "network_configuration_changed=false",
            "boot_environment_changed=false",
            "storage_layout_changed=false",
            "firmware_changed=false",
            "device_unique_addresses_collected=false",
            "credentials_collected=false",
        ):
            self.assertIn(assertion, text)

    def test_parser_rejects_mac_addresses(self):
        text = (
            "goreecloud_router_os_hardware_discovery=0.1\n"
            "profile_id=glinet-gl-mt5000\n"
            "collector_mode=non-mutating\n"
            "privacy=device-unique-identifiers-excluded\n"
            "[network.interfaces]\n"
            "address=aa:bb:cc:dd:ee:ff\n"
            "[collector.boundary]\n"
            "network_configuration_changed=false\n"
            "boot_environment_changed=false\n"
            "storage_layout_changed=false\n"
            "firmware_changed=false\n"
            "device_unique_addresses_collected=false\n"
            "credentials_collected=false\n"
        )
        with self.assertRaises(DiscoveryReportError):
            parse_discovery_report(text)

    def test_parser_rejects_serial_values(self):
        text = (
            "goreecloud_router_os_hardware_discovery=0.1\n"
            "profile_id=glinet-gl-mt5000\n"
            "collector_mode=non-mutating\n"
            "privacy=device-unique-identifiers-excluded\n"
            "[cpu.summary]\n"
            "Serial: 0123456789abcdef\n"
            "[collector.boundary]\n"
            "network_configuration_changed=false\n"
            "boot_environment_changed=false\n"
            "storage_layout_changed=false\n"
            "firmware_changed=false\n"
            "device_unique_addresses_collected=false\n"
            "credentials_collected=false\n"
        )
        with self.assertRaises(DiscoveryReportError):
            parse_discovery_report(text)

    def test_parser_rejects_credential_like_fields(self):
        text = (
            "goreecloud_router_os_hardware_discovery=0.1\n"
            "profile_id=glinet-gl-mt5000\n"
            "collector_mode=non-mutating\n"
            "privacy=device-unique-identifiers-excluded\n"
            "[unsafe]\n"
            "password=example\n"
            "[collector.boundary]\n"
            "network_configuration_changed=false\n"
            "boot_environment_changed=false\n"
            "storage_layout_changed=false\n"
            "firmware_changed=false\n"
            "device_unique_addresses_collected=false\n"
            "credentials_collected=false\n"
        )
        with self.assertRaises(DiscoveryReportError):
            parse_discovery_report(text)

    def test_collector_source_contains_no_mutating_router_commands(self):
        source = COLLECTOR.read_text(encoding="utf-8")
        forbidden = (
            "uci set",
            "uci commit",
            "ip link set",
            "ip addr add",
            "ip addr replace",
            "ip route add",
            "nft add",
            "nft delete",
            "fw_setenv ",
            "mtd write",
            "mtd erase",
            "sysupgrade ",
            "reboot",
            "poweroff",
            "service restart",
            "/etc/init.d/",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, source)

    def test_collector_is_plain_posix_shell_source(self):
        mode = COLLECTOR.stat().st_mode
        self.assertTrue(stat.S_ISREG(mode))
        source = COLLECTOR.read_text(encoding="utf-8")
        self.assertTrue(source.startswith("#!/bin/sh\n"))
        self.assertNotIn("#!/bin/bash", source)


if __name__ == "__main__":
    unittest.main()
