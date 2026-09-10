"""Milestone 0 Router OS architecture prototype and bounded lab execution substrate."""

from .compiler import compile_plan
from .journal import AtomicJournalStore, JournalError, JournalRecord
from .linux_adapter import (
    AdapterError,
    AdapterPlan,
    ExecutionResult,
    LinuxNamespaceExecutionAdapter,
    RenderedCommand,
    TargetValidationError,
    UnsupportedOperation,
)
from .model import ConfigRevision, normalize_config
from .preview import PreviewChange, PreviewReport, preview_changes, preview_matches
from .recovery import RecoveryRequired, RecoveryResult, recover_interrupted_transaction
from .reviewed import PreviewMismatch, apply_reviewed_transaction
from .transaction import InMemoryRuntime, TransactionResult, apply_transaction
from .validator import ValidationError, validate_config

__all__ = [
    "AdapterError",
    "AdapterPlan",
    "AtomicJournalStore",
    "ConfigRevision",
    "ExecutionResult",
    "InMemoryRuntime",
    "JournalError",
    "JournalRecord",
    "LinuxNamespaceExecutionAdapter",
    "PreviewChange",
    "PreviewMismatch",
    "PreviewReport",
    "RecoveryRequired",
    "RecoveryResult",
    "RenderedCommand",
    "TargetValidationError",
    "TransactionResult",
    "UnsupportedOperation",
    "ValidationError",
    "apply_reviewed_transaction",
    "apply_transaction",
    "compile_plan",
    "normalize_config",
    "preview_changes",
    "preview_matches",
    "recover_interrupted_transaction",
    "validate_config",
]
