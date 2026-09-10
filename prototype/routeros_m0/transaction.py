from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping

from .compiler import compile_plan
from .model import ConfigRevision
from .validator import validate_config


@dataclass(frozen=True)
class TransactionResult:
    retained: bool
    rolled_back: bool
    desired_revision: str
    applied_revision: str | None
    observed_revision: str | None
    reason: str


class InMemoryRuntime:
    """Unprivileged runtime used only to prove transaction semantics."""

    def __init__(self, initial_config: Mapping[str, Any] | None = None) -> None:
        self._applied = deepcopy(initial_config) if initial_config is not None else None
        self.force_verification_failure = False

    def snapshot(self) -> dict[str, Any] | None:
        return deepcopy(self._applied)

    def apply(self, desired: Mapping[str, Any], plan: Mapping[str, Any]) -> None:
        # A real adapter would map structured operations to privileged backends.
        # The prototype intentionally stores only the normalized desired config.
        if plan.get("revision") != ConfigRevision.from_config(desired).digest:
            raise RuntimeError("plan revision does not match desired configuration")
        self._applied = deepcopy(desired)

    def observe(self) -> dict[str, Any] | None:
        if self._applied is None:
            return None
        observed = deepcopy(self._applied)
        if self.force_verification_failure:
            observed["ipv4_forwarding"] = not observed.get("ipv4_forwarding", False)
        return observed

    def restore(self, snapshot: Mapping[str, Any] | None) -> None:
        self._applied = deepcopy(snapshot) if snapshot is not None else None


def apply_transaction(config: Mapping[str, Any], runtime: InMemoryRuntime) -> TransactionResult:
    validate_config(config)
    desired = ConfigRevision.from_config(config)
    plan = compile_plan(desired.normalized)
    previous = runtime.snapshot()

    runtime.apply(desired.normalized, plan)
    applied = ConfigRevision.from_config(runtime.snapshot()).digest if runtime.snapshot() is not None else None
    observed_state = runtime.observe()
    observed = ConfigRevision.from_config(observed_state).digest if observed_state is not None else None

    if observed != desired.digest:
        runtime.restore(previous)
        restored = runtime.snapshot()
        restored_digest = ConfigRevision.from_config(restored).digest if restored is not None else None
        return TransactionResult(
            retained=False,
            rolled_back=True,
            desired_revision=desired.digest,
            applied_revision=restored_digest,
            observed_revision=observed,
            reason="verification failed; previous state restored",
        )

    return TransactionResult(
        retained=True,
        rolled_back=False,
        desired_revision=desired.digest,
        applied_revision=applied,
        observed_revision=observed,
        reason="verification matched desired revision",
    )
