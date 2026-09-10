from __future__ import annotations

from typing import Any, Mapping

from .journal import AtomicJournalStore
from .preview import PreviewReport, preview_changes
from .transaction import InMemoryRuntime, TransactionResult, apply_transaction


class PreviewMismatch(RuntimeError):
    """Raised when the reviewed preview no longer matches the apply candidate."""


def apply_reviewed_transaction(
    config: Mapping[str, Any],
    runtime: InMemoryRuntime,
    reviewed_preview: PreviewReport,
    *,
    journal_store: AtomicJournalStore | None = None,
) -> TransactionResult:
    """Apply only when the exact previous/desired pair matches the reviewed preview.

    This is the Milestone 0 orchestration path for Preview -> Apply consistency.
    It intentionally delegates to the existing unprivileged transaction proof
    and does not add a privileged Linux networking executor.
    """
    current_preview = preview_changes(config, runtime.snapshot())
    if current_preview.approval_token != reviewed_preview.approval_token:
        raise PreviewMismatch("reviewed preview no longer matches the current previous/desired configuration revisions")
    return apply_transaction(config, runtime, journal_store=journal_store)
