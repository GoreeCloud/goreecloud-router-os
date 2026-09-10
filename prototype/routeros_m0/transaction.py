from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping

from .compiler import compile_plan
from .journal import AtomicJournalStore, JournalRecord
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


def _digest(config: Mapping[str, Any] | None) -> str | None:
    return ConfigRevision.from_config(config).digest if config is not None else None


def apply_transaction(
    config: Mapping[str, Any],
    runtime: InMemoryRuntime,
    *,
    journal_store: AtomicJournalStore | None = None,
) -> TransactionResult:
    """Validate, apply, verify, and retain or roll back a candidate config.

    When a journal store is supplied, phase transitions are written atomically
    before and after the in-memory apply so a later process can reconcile an
    interrupted transaction without guessing.
    """
    validate_config(config)
    desired = ConfigRevision.from_config(config)
    plan = compile_plan(desired.normalized)
    previous = runtime.snapshot()
    previous_digest = _digest(previous)
    record = JournalRecord.prepare(desired.normalized, previous) if journal_store is not None else None

    if journal_store is not None and record is not None:
        journal_store.write(record)

    try:
        runtime.apply(desired.normalized, plan)
    except Exception:
        runtime.restore(previous)
        if journal_store is not None and record is not None:
            journal_store.write(record.with_phase("rolled_back"))
            if _digest(runtime.snapshot()) == previous_digest:
                journal_store.clear()
        raise

    applied_snapshot = runtime.snapshot()
    applied = _digest(applied_snapshot)
    if journal_store is not None and record is not None:
        journal_store.write(record.with_phase("applied"))

    observed_state = runtime.observe()
    observed = _digest(observed_state)

    if observed != desired.digest:
        runtime.restore(previous)
        restored_digest = _digest(runtime.snapshot())
        if journal_store is not None and record is not None:
            journal_store.write(record.with_phase("rolled_back"))
            if restored_digest == previous_digest:
                journal_store.clear()
        return TransactionResult(
            retained=False,
            rolled_back=True,
            desired_revision=desired.digest,
            applied_revision=restored_digest,
            observed_revision=observed,
            reason="verification failed; previous state restored",
        )

    if journal_store is not None and record is not None:
        journal_store.write(record.with_phase("retained"))
        journal_store.clear()

    return TransactionResult(
        retained=True,
        rolled_back=False,
        desired_revision=desired.digest,
        applied_revision=applied,
        observed_revision=observed,
        reason="verification matched desired revision",
    )
