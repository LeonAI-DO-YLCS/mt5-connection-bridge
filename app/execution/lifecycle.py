"""Deterministic operation lifecycle for trade-affecting operations.

Every trade-affecting route transitions through named states:
queued → dispatching → accepted | rejected | recovered | failed_terminal

See spec FR-001 through FR-003.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum

from ..messaging.tracking import generate_tracking_id

logger = logging.getLogger("mt5_bridge.execution.lifecycle")


class OperationState(StrEnum):
    """Named states for trade-affecting operations (FR-001)."""

    QUEUED = "queued"
    DISPATCHING = "dispatching"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    RECOVERED = "recovered"
    FAILED_TERMINAL = "failed_terminal"


# Terminal states — once reached, no further transitions are valid.
_TERMINAL_STATES = frozenset({
    OperationState.ACCEPTED,
    OperationState.REJECTED,
    OperationState.RECOVERED,
    OperationState.FAILED_TERMINAL,
})


@dataclass
class OperationContext:
    """Tracks the full lifecycle of a single trade-affecting operation (FR-018)."""

    tracking_id: str
    operation: str
    state_transitions: list[OperationState] = field(default_factory=list)
    current_state: OperationState = OperationState.QUEUED
    idempotency_key: str | None = None
    retry_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    request_hash: str | None = None

    def __post_init__(self) -> None:
        """Append the initial state to transitions."""
        if not self.state_transitions:
            self.state_transitions.append(self.current_state)


def create_context(
    operation: str,
    *,
    idempotency_key: str | None = None,
    request_hash: str | None = None,
) -> OperationContext:
    """Factory: create a new OperationContext starting in QUEUED state."""
    return OperationContext(
        tracking_id=generate_tracking_id(),
        operation=operation,
        idempotency_key=idempotency_key,
        request_hash=request_hash,
    )


def transition(ctx: OperationContext, new_state: OperationState) -> None:
    """Advance the operation to a new state (FR-002).

    Appends to ``state_transitions`` and updates ``current_state``.
    Logs the transition for observability.

    Raises ValueError if the current state is already terminal.
    """
    if ctx.current_state in _TERMINAL_STATES:
        raise ValueError(
            f"Cannot transition from terminal state '{ctx.current_state}' "
            f"to '{new_state}' (tracking_id={ctx.tracking_id})"
        )
    ctx.state_transitions.append(new_state)
    ctx.current_state = new_state
    logger.debug(
        "Lifecycle transition: %s → %s (tracking_id=%s, operation=%s)",
        ctx.state_transitions[-2] if len(ctx.state_transitions) >= 2 else "?",
        new_state,
        ctx.tracking_id,
        ctx.operation,
    )
