from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

from .model import ConfigRevision
from .validator import validate_config

RISK_ORDER = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


@dataclass(frozen=True)
class PreviewChange:
    area: str
    field: str
    risk: str
    summary: str


@dataclass(frozen=True)
class PreviewReport:
    preview_version: str
    previous_revision: str | None
    desired_revision: str
    risk: str
    requires_connectivity_confirmation: bool
    changes: tuple[PreviewChange, ...]
    approval_token: str


def _approval_token(previous_revision: str | None, desired_revision: str, changes: tuple[PreviewChange, ...]) -> str:
    payload = {
        "preview_version": "0.1",
        "previous_revision": previous_revision,
        "desired_revision": desired_revision,
        "changes": [change.__dict__ for change in changes],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _role_map(config: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {item["role"]: item for item in config["interfaces"]}


def _add(changes: list[PreviewChange], area: str, field: str, risk: str, summary: str) -> None:
    changes.append(PreviewChange(area=area, field=field, risk=risk, summary=summary))


def preview_changes(desired: Mapping[str, Any], previous: Mapping[str, Any] | None = None) -> PreviewReport:
    """Build a deterministic, privacy-safe change preview for Reference Build 0.1.

    The report contains only known semantic change descriptions and revision
    identities. It never includes raw configuration objects, addresses, DHCP
    values, credentials, tokens, keys, packet data, DNS history, or telemetry.
    """
    validate_config(desired)
    desired_revision = ConfigRevision.from_config(desired)
    previous_revision = ConfigRevision.from_config(previous) if previous is not None else None
    changes: list[PreviewChange] = []

    if previous is None:
        _add(changes, "system", "initial_configuration", "high", "Initial router configuration will replace an unconfigured runtime state.")
    else:
        validate_config(previous)
        old_roles = _role_map(previous_revision.normalized)
        new_roles = _role_map(desired_revision.normalized)

        for role in ("wan", "lan"):
            old = old_roles[role]
            new = new_roles[role]
            if old["name"] != new["name"]:
                _add(changes, "interface", f"{role}.name", "high" if role == "lan" else "medium", f"{role.upper()} interface binding will change.")
            if old["mode"] != new["mode"]:
                _add(changes, "interface", f"{role}.mode", "high", f"{role.upper()} addressing mode will change.")
            if old.get("address") != new.get("address"):
                _add(changes, "interface", f"{role}.address", "critical" if role == "lan" else "high", f"{role.upper()} interface address will change.")

        old_lan = old_roles["lan"]
        new_lan = new_roles["lan"]
        for field in ("start", "end"):
            if old_lan["dhcp"][field] != new_lan["dhcp"][field]:
                _add(changes, "dhcp", field, "medium", "LAN DHCP allocation range will change.")
        if old_lan["dhcp"]["lease_seconds"] != new_lan["dhcp"]["lease_seconds"]:
            _add(changes, "dhcp", "lease_seconds", "low", "LAN DHCP lease duration will change.")

        old_fw = previous_revision.normalized["firewall"]
        new_fw = desired_revision.normalized["firewall"]
        for field in ("default_input", "default_forward", "allow_established", "allow_lan_to_wan"):
            if old_fw[field] != new_fw[field]:
                _add(changes, "firewall", field, "high", "Firewall policy behavior will change.")

        old_mgmt = previous_revision.normalized["management"]
        new_mgmt = desired_revision.normalized["management"]
        for field in ("bind_role", "authenticated"):
            if old_mgmt[field] != new_mgmt[field]:
                _add(changes, "management", field, "critical", "Administrative access policy will change.")

        if previous_revision.normalized["ipv4_forwarding"] != desired_revision.normalized["ipv4_forwarding"]:
            _add(changes, "routing", "ipv4_forwarding", "high", "IPv4 forwarding behavior will change.")

    changes.sort(key=lambda item: (item.area, item.field, item.summary))
    frozen_changes = tuple(changes)
    overall = max((change.risk for change in frozen_changes), key=RISK_ORDER.get, default="none")
    confirmation = any(RISK_ORDER[change.risk] >= RISK_ORDER["high"] for change in frozen_changes)
    previous_digest = previous_revision.digest if previous_revision is not None else None
    return PreviewReport(
        preview_version="0.1",
        previous_revision=previous_digest,
        desired_revision=desired_revision.digest,
        risk=overall,
        requires_connectivity_confirmation=confirmation,
        changes=frozen_changes,
        approval_token=_approval_token(previous_digest, desired_revision.digest, frozen_changes),
    )


def preview_matches(report: PreviewReport, desired: Mapping[str, Any], previous: Mapping[str, Any] | None = None) -> bool:
    return preview_changes(desired, previous).approval_token == report.approval_token
