"""Structured observability logging for trade-affecting operations (FR-018).

Every trade-affecting operation attempt produces a structured log entry
containing: tracking_id, operation, state_transition, code, retry_count,
idempotency_key, and final_outcome.
"""

from __future__ import annotations

import logging

from .lifecycle import OperationContext

logger = logging.getLogger("mt5_bridge.execution.observability")


def emit_operation_log(
    ctx: OperationContext,
    code: str,
    final_outcome: str,
) -> None:
    """Emit a structured log entry for a completed operation (FR-018).

    Args:
        ctx: The operation context with lifecycle data.
        code: The canonical error code name (e.g., "REQUEST_OK").
        final_outcome: Human-readable outcome string (e.g., "fill_confirmed").
    """
    log_data = {
        "tracking_id": ctx.tracking_id,
        "operation": ctx.operation,
        "state_transition": " → ".join(str(s) for s in ctx.state_transitions),
        "code": code,
        "retry_count": ctx.retry_count,
        "idempotency_key": ctx.idempotency_key,
        "final_outcome": final_outcome,
    }
    logger.info("Operation complete: %s", log_data)
