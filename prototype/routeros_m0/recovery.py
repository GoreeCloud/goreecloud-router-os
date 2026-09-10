from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from .journal import AtomicJournalStore, JournalError
from .model import ConfigRevision


class ObservableRuntime(Protocol):
    def observe(self) -> dict[str, Any] | None: ...


class RecoveryRequired(RuntimeError):
    """Raised when recovery cannot safely choose a known state automatically."""


@dataclass(frozen=True)
class RecoveryResult:
    action: str
    journal_phase: str | None
    runtime_revision: str | None
    reason: str


def _revision(config: Mapping[str, Any] | None) -> str | None:
    return ConfigRevision.from_config(config).digest if config is not None else None


def recover_interrupted_transaction(store: AtomicJournalStore, runtime: ObservableRuntime) -> RecoveryResult:
    """Reconcile an interrupted Milestone 0 transaction without guessing.

    Only exact previous or desired revisions are accepted automatically. Any
    third state remains untouched and requires explicit recovery work.
    """
    try:
        record = store.read()
    except JournalError as exc:
        raise RecoveryRequired("journal integrity is not trustworthy; automatic recovery refused") from exc

    if record is None:
        return RecoveryResult(action="none", journal_phase=None, runtime_revision=_revision(runtime.observe()), reason="no journal present")

    observed = runtime.observe()
    observed_revision = _revision(observed)

    if record.phase == "prepared":
        if observed_revision == record.previous_revision:
            store.clear()
            return RecoveryResult(
                action="discarded-unapplied",
                journal_phase="prepared",
                runtime_revision=observed_revision,
                reason="runtime still matches previous revision; no apply was observed",
            )
        if observed_revision == record.desired_revision:
            store.write(record.with_phase("retained"))
            store.clear()
            return RecoveryResult(
                action="retained-desired",
                journal_phase="prepared",
                runtime_revision=observed_revision,
                reason="desired revision is already observed; interrupted journal finalized",
            )

    if record.phase == "applied":
        if observed_revision == record.desired_revision:
            store.write(record.with_phase("retained"))
            store.clear()
            return RecoveryResult(
                action="retained-desired",
                journal_phase="applied",
                runtime_revision=observed_revision,
                reason="applied desired revision is observed and retained",
            )
        if observed_revision == record.previous_revision:
            store.write(record.with_phase("rolled_back"))
            store.clear()
            return RecoveryResult(
                action="confirmed-rollback",
                journal_phase="applied",
                runtime_revision=observed_revision,
                reason="runtime already matches the previous known-good revision",
            )

    if record.phase == "retained" and observed_revision == record.desired_revision:
        store.clear()
        return RecoveryResult(
            action="cleared-terminal",
            journal_phase="retained",
            runtime_revision=observed_revision,
            reason="terminal retained journal matches runtime",
        )

    if record.phase == "rolled_back" and observed_revision == record.previous_revision:
        store.clear()
        return RecoveryResult(
            action="cleared-terminal",
            journal_phase="rolled_back",
            runtime_revision=observed_revision,
            reason="terminal rollback journal matches runtime",
        )

    raise RecoveryRequired(
        "runtime is neither the exact previous nor desired revision allowed by the journal; automatic overwrite refused"
    )
