"""Execution package re-exports for convenient imports.

Usage::
    from app.execution import create_context, transition, OperationState
    from app.execution import idempotency_store, compute_request_hash
    from app.execution import SingleFlightGuard
    from app.execution import emit_operation_log
"""

from .lifecycle import OperationContext, OperationState, create_context, transition
from .idempotency import IdempotencyStore, compute_request_hash, idempotency_store
from .single_flight import SingleFlightGuard
from .observability import emit_operation_log

__all__ = [
    "OperationContext",
    "OperationState",
    "create_context",
    "transition",
    "IdempotencyStore",
    "compute_request_hash",
    "idempotency_store",
    "SingleFlightGuard",
    "emit_operation_log",
]
