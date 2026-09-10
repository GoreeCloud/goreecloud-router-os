from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import hmac
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping
from uuid import uuid4

from .model import ConfigRevision, normalize_config

JOURNAL_VERSION = "0.1"
PHASES = {"prepared", "applied", "retained", "rolled_back"}
SENSITIVE_KEYS = {
    "api_key",
    "credential",
    "credentials",
    "password",
    "private_key",
    "recovery_code",
    "secret",
    "token",
}


class JournalError(RuntimeError):
    """Raised when a journal cannot be safely trusted or persisted."""


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _assert_no_sensitive_fields(value: Any, path: str = "config") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized_key = str(key).strip().lower()
            if normalized_key in SENSITIVE_KEYS:
                raise JournalError(f"refusing to persist sensitive field at {path}.{key}")
            _assert_no_sensitive_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_no_sensitive_fields(child, f"{path}[{index}]")


def _digest_or_none(config: Mapping[str, Any] | None) -> str | None:
    return ConfigRevision.from_config(config).digest if config is not None else None


@dataclass(frozen=True)
class JournalRecord:
    transaction_id: str
    phase: str
    desired_config: dict[str, Any]
    previous_config: dict[str, Any] | None
    desired_revision: str
    previous_revision: str | None

    @classmethod
    def prepare(
        cls,
        desired: Mapping[str, Any],
        previous: Mapping[str, Any] | None,
        *,
        transaction_id: str | None = None,
    ) -> "JournalRecord":
        desired_normalized = normalize_config(desired)
        previous_normalized = normalize_config(previous) if previous is not None else None
        _assert_no_sensitive_fields(desired_normalized, "desired_config")
        if previous_normalized is not None:
            _assert_no_sensitive_fields(previous_normalized, "previous_config")
        return cls(
            transaction_id=transaction_id or uuid4().hex,
            phase="prepared",
            desired_config=desired_normalized,
            previous_config=previous_normalized,
            desired_revision=ConfigRevision.from_config(desired_normalized).digest,
            previous_revision=_digest_or_none(previous_normalized),
        )

    def with_phase(self, phase: str) -> "JournalRecord":
        if phase not in PHASES:
            raise JournalError(f"unsupported journal phase: {phase}")
        return replace(self, phase=phase)

    def payload(self) -> dict[str, Any]:
        if self.phase not in PHASES:
            raise JournalError(f"unsupported journal phase: {self.phase}")
        _assert_no_sensitive_fields(self.desired_config, "desired_config")
        if self.previous_config is not None:
            _assert_no_sensitive_fields(self.previous_config, "previous_config")
        if ConfigRevision.from_config(self.desired_config).digest != self.desired_revision:
            raise JournalError("desired configuration does not match desired_revision")
        if _digest_or_none(self.previous_config) != self.previous_revision:
            raise JournalError("previous configuration does not match previous_revision")
        return {
            "journal_version": JOURNAL_VERSION,
            "transaction_id": self.transaction_id,
            "phase": self.phase,
            "desired_config": self.desired_config,
            "previous_config": self.previous_config,
            "desired_revision": self.desired_revision,
            "previous_revision": self.previous_revision,
        }


class AtomicJournalStore:
    """Atomic, integrity-checked local journal for the Milestone 0 proof.

    This store is deliberately limited to the current secret-free reference
    configuration. It is not an Everkeep implementation or a production secret
    store.
    """

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path)

    def exists(self) -> bool:
        return self.path.exists()

    def write(self, record: JournalRecord) -> None:
        payload = record.payload()
        envelope = dict(payload)
        envelope["checksum"] = hashlib.sha256(_canonical_json(payload)).hexdigest()
        encoded = json.dumps(envelope, sort_keys=True, indent=2, ensure_ascii=False) + "\n"

        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=f".{self.path.name}.", suffix=".tmp", dir=self.path.parent)
        temp_path = Path(temp_name)
        try:
            os.chmod(temp_path, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, self.path)
            os.chmod(self.path, 0o600)
            self._fsync_parent()
        except Exception:
            try:
                temp_path.unlink(missing_ok=True)
            finally:
                raise

    def read(self) -> JournalRecord | None:
        if not self.path.exists():
            return None
        try:
            envelope = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise JournalError("transaction journal is unreadable") from exc
        if not isinstance(envelope, dict):
            raise JournalError("transaction journal must contain a JSON object")

        expected_keys = {"journal_version", "transaction_id", "phase", "desired_config", "previous_config", "desired_revision", "previous_revision", "checksum"}
        if set(envelope) != expected_keys:
            raise JournalError("transaction journal fields are invalid")

        checksum = envelope.pop("checksum", None)
        if not isinstance(checksum, str):
            raise JournalError("transaction journal checksum is missing")
        expected = hashlib.sha256(_canonical_json(envelope)).hexdigest()
        if not hmac.compare_digest(checksum, expected):
            raise JournalError("transaction journal checksum mismatch")
        if envelope.get("journal_version") != JOURNAL_VERSION:
            raise JournalError("unsupported transaction journal version")

        phase = envelope.get("phase")
        if phase not in PHASES:
            raise JournalError("unsupported transaction journal phase")
        transaction_id = envelope.get("transaction_id")
        if not isinstance(transaction_id, str) or not transaction_id:
            raise JournalError("transaction journal transaction_id is invalid")
        desired_config = envelope.get("desired_config")
        previous_config = envelope.get("previous_config")
        if not isinstance(desired_config, dict):
            raise JournalError("transaction journal desired_config is invalid")
        if previous_config is not None and not isinstance(previous_config, dict):
            raise JournalError("transaction journal previous_config is invalid")

        record = JournalRecord(
            transaction_id=transaction_id,
            phase=phase,
            desired_config=desired_config,
            previous_config=previous_config,
            desired_revision=envelope.get("desired_revision"),
            previous_revision=envelope.get("previous_revision"),
        )
        record.payload()
        return record

    def clear(self) -> None:
        try:
            self.path.unlink()
        except FileNotFoundError:
            return
        self._fsync_parent()

    def _fsync_parent(self) -> None:
        flags = getattr(os, "O_DIRECTORY", 0) | os.O_RDONLY
        try:
            directory_fd = os.open(self.path.parent, flags)
        except OSError:
            return
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
