"""MT5 Bridge — Message normalization factories.

``normalize_error()`` and ``normalize_success()`` are the single entry points
for constructing canonical ``MessageEnvelope`` instances.  All exception
handlers and route-level error builders delegate here.
"""

from __future__ import annotations

from typing import Any

from .codes import ErrorCode
from .envelope import MessageEnvelope, _sanitize_context
from .tracking import generate_tracking_id


def normalize_error(
    code: ErrorCode,
    *,
    message: str | None = None,
    action: str | None = None,
    context: dict[str, Any] | None = None,
    detail: Any = None,
) -> MessageEnvelope:
    """Build a canonical error envelope from an ``ErrorCode``.

    Parameters
    ----------
    code:
        The semantic error code.
    message:
        Override for the default message text.
    action:
        Override for the default action text.
    context:
        Technical hints (will be sanitized — sensitive keys stripped).
    detail:
        Legacy ``detail`` value for backward compatibility.

    Returns
    -------
    MessageEnvelope
        A fully-populated error envelope with a fresh ``tracking_id``.
    """
    meta = code.value
    resolved_message = message or meta.default_message
    return MessageEnvelope(
        ok=False,
        category=meta.category,
        code=code.name,
        tracking_id=generate_tracking_id(),
        title=meta.default_title,
        message=resolved_message,
        action=action or meta.default_action,
        severity=meta.default_severity,
        retryable=meta.default_retryable,
        context=_sanitize_context(context),
        detail=detail if detail is not None else resolved_message,
    )


def normalize_success(
    *,
    title: str = "Operation completed successfully",
    message: str = "The operation completed without errors.",
    data: dict[str, Any] | None = None,
) -> MessageEnvelope:
    """Build a canonical success envelope.

    Parameters
    ----------
    title:
        Concise success summary (≤ 80 chars).
    message:
        Plain-English explanation of the successful outcome.
    data:
        Trade-specific result data (filled_price, ticket_id, etc.).

    Returns
    -------
    MessageEnvelope
        A fully-populated success envelope with a fresh ``tracking_id``.
    """
    return MessageEnvelope(
        ok=True,
        category="success",
        code=ErrorCode.REQUEST_OK.name,
        tracking_id=generate_tracking_id(),
        title=title,
        message=message,
        action="No action required.",
        severity="low",
        retryable=False,
        context={},
        detail=title,
        data=data,
    )
