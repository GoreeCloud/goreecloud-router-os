from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping


class HardwareProfileError(ValueError):
    """Raised when a Router OS hardware profile is malformed or unsafe."""


@dataclass(frozen=True)
class HardwareReadiness:
    profile_id: str
    installable: bool
    blockers: tuple[str, ...]


_REQUIRED_TOP_LEVEL = {
    "profile_version",
    "profile_id",
    "vendor",
    "model",
    "product_name",
    "architecture",
    "lifecycle",
    "resources",
    "ethernet",
    "storage",
    "platform",
    "evidence",
    "unknowns",
}


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise HardwareProfileError(f"{field} must be an object")
    return value


def _require_nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HardwareProfileError(f"{field} must be a non-empty string")
    return value.strip()


def _require_bool(value: Any, field: str) -> bool:
    if type(value) is not bool:
        raise HardwareProfileError(f"{field} must be a boolean")
    return value


def validate_hardware_profile(profile: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a Development hardware profile without promoting support state."""
    data = dict(_require_mapping(profile, "profile"))
    missing = sorted(_REQUIRED_TOP_LEVEL - data.keys())
    if missing:
        raise HardwareProfileError(
            f"hardware profile is missing required fields: {', '.join(missing)}"
        )

    if data["profile_version"] != "0.1":
        raise HardwareProfileError("unsupported hardware profile version")

    _require_nonempty_string(data["profile_id"], "profile_id")
    _require_nonempty_string(data["vendor"], "vendor")
    _require_nonempty_string(data["model"], "model")
    _require_nonempty_string(data["product_name"], "product_name")

    if data["architecture"] not in {"x86_64", "aarch64"}:
        raise HardwareProfileError("architecture must be x86_64 or aarch64")

    lifecycle = _require_mapping(data["lifecycle"], "lifecycle")
    status = _require_nonempty_string(lifecycle.get("status"), "lifecycle.status")
    if status not in {"research", "development", "experimental", "supported"}:
        raise HardwareProfileError("lifecycle.status is not recognized")
    installable = _require_bool(lifecycle.get("installable"), "lifecycle.installable")
    supported = _require_bool(lifecycle.get("supported"), "lifecycle.supported")
    hardware_verified = _require_bool(
        lifecycle.get("hardware_verified"),
        "lifecycle.hardware_verified",
    )
    if supported and status != "supported":
        raise HardwareProfileError("supported=true requires lifecycle.status=supported")
    if supported and not installable:
        raise HardwareProfileError("supported hardware must be installable")
    if installable and not hardware_verified:
        raise HardwareProfileError("installable=true requires hardware_verified=true")

    resources = _require_mapping(data["resources"], "resources")
    cpu = _require_mapping(resources.get("cpu"), "resources.cpu")
    if type(cpu.get("cores")) is not int or cpu["cores"] <= 0:
        raise HardwareProfileError("resources.cpu.cores must be a positive integer")
    if (
        type(cpu.get("max_frequency_mhz")) is not int
        or cpu["max_frequency_mhz"] <= 0
    ):
        raise HardwareProfileError(
            "resources.cpu.max_frequency_mhz must be a positive integer"
        )
    _require_nonempty_string(
        resources.get("memory_vendor_capacity"),
        "resources.memory_vendor_capacity",
    )

    ethernet = _require_mapping(data["ethernet"], "ethernet")
    ports = ethernet.get("ports")
    if not isinstance(ports, list) or not ports:
        raise HardwareProfileError("ethernet.ports must be a non-empty list")
    seen_labels: set[str] = set()
    for index, port in enumerate(ports):
        item = _require_mapping(port, f"ethernet.ports[{index}]")
        label = _require_nonempty_string(
            item.get("label"),
            f"ethernet.ports[{index}].label",
        )
        if label in seen_labels:
            raise HardwareProfileError("ethernet port labels must be unique")
        seen_labels.add(label)
        if (
            type(item.get("max_speed_mbps")) is not int
            or item["max_speed_mbps"] <= 0
        ):
            raise HardwareProfileError(
                f"ethernet.ports[{index}].max_speed_mbps must be a positive integer"
            )
        kernel_name = item.get("kernel_name")
        if kernel_name is not None and (
            not isinstance(kernel_name, str) or not kernel_name
        ):
            raise HardwareProfileError(
                f"ethernet.ports[{index}].kernel_name must be null or a non-empty string"
            )
        _require_bool(
            item.get("observed_on_target"),
            f"ethernet.ports[{index}].observed_on_target",
        )

    storage = _require_mapping(data["storage"], "storage")
    _require_nonempty_string(storage.get("type"), "storage.type")
    _require_nonempty_string(storage.get("vendor_capacity"), "storage.vendor_capacity")
    _require_bool(
        storage.get("partition_map_verified"),
        "storage.partition_map_verified",
    )

    platform = _require_mapping(data["platform"], "platform")
    for field in (
        "boot_chain_verified",
        "recovery_path_verified",
        "device_tree_verified",
        "kernel_support_verified",
        "watchdog_verified",
        "thermal_monitoring_verified",
    ):
        _require_bool(platform.get(field), f"platform.{field}")

    evidence = data["evidence"]
    if not isinstance(evidence, list) or not evidence:
        raise HardwareProfileError("evidence must contain at least one source")
    for index, source in enumerate(evidence):
        item = _require_mapping(source, f"evidence[{index}]")
        if item.get("class") not in {
            "vendor-primary",
            "upstream-primary",
            "direct-observation",
            "test-result",
        }:
            raise HardwareProfileError(f"evidence[{index}].class is not recognized")
        _require_nonempty_string(item.get("url"), f"evidence[{index}].url")
        _require_nonempty_string(
            item.get("supports"),
            f"evidence[{index}].supports",
        )

    unknowns = data["unknowns"]
    if not isinstance(unknowns, list):
        raise HardwareProfileError("unknowns must be a list")
    for index, item in enumerate(unknowns):
        _require_nonempty_string(item, f"unknowns[{index}]")

    if installable:
        readiness = assess_hardware_readiness(data)
        if readiness.blockers:
            raise HardwareProfileError(
                "installable hardware profile still has blockers: "
                + "; ".join(readiness.blockers)
            )

    return data


def load_hardware_profile(path: str | Path) -> dict[str, Any]:
    profile_path = Path(path)
    try:
        payload = json.loads(profile_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HardwareProfileError(
            f"unable to load hardware profile: {profile_path}"
        ) from exc
    return validate_hardware_profile(payload)


def assess_hardware_readiness(profile: Mapping[str, Any]) -> HardwareReadiness:
    """Return fail-closed blockers for physical installation readiness."""
    data = dict(_require_mapping(profile, "profile"))
    profile_id = _require_nonempty_string(data.get("profile_id"), "profile_id")
    blockers: list[str] = []

    lifecycle = _require_mapping(data.get("lifecycle"), "lifecycle")
    if lifecycle.get("hardware_verified") is not True:
        blockers.append("target hardware has not been directly verified")

    ethernet = _require_mapping(data.get("ethernet"), "ethernet")
    ports = ethernet.get("ports")
    if not isinstance(ports, list) or not ports:
        blockers.append("Ethernet port inventory is unavailable")
    else:
        for port in ports:
            if not isinstance(port, Mapping):
                blockers.append("Ethernet port entry is malformed")
                continue
            label = str(port.get("label") or "unknown")
            if not port.get("kernel_name"):
                blockers.append(f"{label} Linux interface binding is unknown")
            if port.get("observed_on_target") is not True:
                blockers.append(f"{label} has not been observed on target hardware")

    storage = _require_mapping(data.get("storage"), "storage")
    if storage.get("partition_map_verified") is not True:
        blockers.append("eMMC partition map has not been verified")

    platform = _require_mapping(data.get("platform"), "platform")
    checks = (
        ("boot_chain_verified", "boot chain has not been verified"),
        ("recovery_path_verified", "recovery path has not been verified"),
        ("device_tree_verified", "device-tree binding has not been verified"),
        ("kernel_support_verified", "kernel support has not been verified"),
        ("watchdog_verified", "watchdog behavior has not been verified"),
        (
            "thermal_monitoring_verified",
            "thermal monitoring has not been verified",
        ),
    )
    for field, message in checks:
        if platform.get(field) is not True:
            blockers.append(message)

    unknowns = data.get("unknowns")
    if not isinstance(unknowns, list):
        blockers.append("hardware unknowns are not represented")
    elif unknowns:
        blockers.append("hardware profile still contains unresolved unknowns")

    return HardwareReadiness(
        profile_id=profile_id,
        installable=not blockers,
        blockers=tuple(blockers),
    )
