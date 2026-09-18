from __future__ import annotations

from dataclasses import dataclass
import re


class DiscoveryReportError(ValueError):
    """Raised when a hardware discovery report violates the evidence contract."""


@dataclass(frozen=True)
class DiscoveryReport:
    version: str
    profile_id: str
    collector_mode: str
    sections: tuple[str, ...]
    text: str


_MAC_RE = re.compile(r"(?i)(?<![0-9a-f])(?:[0-9a-f]{2}:){5}[0-9a-f]{2}(?![0-9a-f])")
_SECRET_RE = re.compile(
    r"(?i)(password|passwd|private[_ -]?key|authorization|bearer[ ]+[a-z0-9._-]+|"
    r"access[_ -]?token|refresh[_ -]?token|api[_ -]?key)"
)
_SERIAL_VALUE_RE = re.compile(r"(?i)^\s*serial(?: number)?\s*[:=]\s*\S+", re.MULTILINE)
_REQUIRED_BOUNDARY = {
    "network_configuration_changed=false",
    "boot_environment_changed=false",
    "storage_layout_changed=false",
    "firmware_changed=false",
    "device_unique_addresses_collected=false",
    "credentials_collected=false",
}


def parse_discovery_report(text: str) -> DiscoveryReport:
    if not isinstance(text, str) or not text.strip():
        raise DiscoveryReportError("discovery report must be non-empty text")

    headers: dict[str, str] = {}
    sections: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("[") and line.endswith("]") and len(line) > 2:
            sections.append(line[1:-1])
            continue
        if sections:
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            headers[key.strip()] = value.strip()

    if headers.get("goreecloud_router_os_hardware_discovery") != "0.1":
        raise DiscoveryReportError("unsupported or missing discovery report version")
    if headers.get("profile_id") != "glinet-gl-mt5000":
        raise DiscoveryReportError("report is not for the GL-MT5000 profile")
    if headers.get("collector_mode") != "non-mutating":
        raise DiscoveryReportError("collector_mode must be non-mutating")
    if headers.get("privacy") != "device-unique-identifiers-excluded":
        raise DiscoveryReportError("privacy boundary is missing")

    if _MAC_RE.search(text):
        raise DiscoveryReportError("report contains a device-unique MAC address")
    if _SECRET_RE.search(text):
        raise DiscoveryReportError("report contains a credential-like value or field")
    if _SERIAL_VALUE_RE.search(text):
        raise DiscoveryReportError("report contains a serial-number value")

    lines = {line.strip() for line in text.splitlines()}
    missing = sorted(_REQUIRED_BOUNDARY - lines)
    if missing:
        raise DiscoveryReportError(
            "report is missing collector-boundary assertions: " + ", ".join(missing)
        )

    if "collector.boundary" not in sections:
        raise DiscoveryReportError("report is missing collector.boundary section")

    return DiscoveryReport(
        version="0.1",
        profile_id=headers["profile_id"],
        collector_mode=headers["collector_mode"],
        sections=tuple(sections),
        text=text,
    )


def report_has_hardware_identity(report: DiscoveryReport) -> bool:
    """Return true when the report includes both model and board-name evidence."""
    present = set(report.sections)
    return "board.model" in present and "board.name" in present


@dataclass(frozen=True)
class GLMT5000Observations:
    model: str | None
    board_name: str | None
    devicetree_model: str | None
    compatibles: tuple[str, ...]
    interfaces: tuple[str, ...]
    block_devices: tuple[str, ...]
    watchdogs: tuple[str, ...]
    thermal_zones: tuple[str, ...]


def section_lines(report: DiscoveryReport, name: str) -> tuple[str, ...]:
    """Return non-empty payload lines from one named report section."""
    active: str | None = None
    values: list[str] = []
    for raw_line in report.text.splitlines():
        line = raw_line.rstrip("\n")
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]") and len(stripped) > 2:
            active = stripped[1:-1]
            continue
        if active == name and stripped:
            values.append(stripped)
    return tuple(values)


def _first_section_value(report: DiscoveryReport, name: str) -> str | None:
    values = section_lines(report, name)
    return values[0] if values else None


def _prefixed_values(report: DiscoveryReport, name: str, prefix: str) -> tuple[str, ...]:
    values: list[str] = []
    for line in section_lines(report, name):
        if line.startswith(prefix):
            value = line[len(prefix):].strip()
            if value:
                values.append(value)
    return tuple(values)


def extract_gl_mt5000_observations(report: DiscoveryReport) -> GLMT5000Observations:
    """Extract privacy-safe direct observations without promoting support state."""
    if report.profile_id != "glinet-gl-mt5000":
        raise DiscoveryReportError("observation extractor requires the GL-MT5000 profile")

    return GLMT5000Observations(
        model=_first_section_value(report, "board.model"),
        board_name=_first_section_value(report, "board.name"),
        devicetree_model=_first_section_value(report, "devicetree.model"),
        compatibles=section_lines(report, "devicetree.compatible"),
        interfaces=_prefixed_values(report, "network.interfaces", "interface="),
        block_devices=_prefixed_values(report, "storage.sysfs", "device="),
        watchdogs=_prefixed_values(report, "watchdog", "watchdog="),
        thermal_zones=_prefixed_values(report, "thermal", "zone="),
    )
