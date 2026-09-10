from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping


def normalize_config(config: Mapping[str, Any]) -> dict[str, Any]:
    """Return a JSON-compatible, deterministically ordered copy of config."""
    encoded = json.dumps(config, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return json.loads(encoded)


@dataclass(frozen=True)
class ConfigRevision:
    normalized: dict[str, Any]
    digest: str

    @classmethod
    def from_config(cls, config: Mapping[str, Any]) -> "ConfigRevision":
        normalized = normalize_config(config)
        payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        return cls(normalized=normalized, digest=digest)
