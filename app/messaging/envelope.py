"""MT5 Bridge — Canonical message envelope and exception.

``MessageEnvelope`` is the Pydantic v2 model for every user-facing response
from trade-affecting endpoints.  ``MessageEnvelopeException`` is a FastAPI
``HTTPException`` subclass that routes can raise to trigger canonical
error responses.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel, Field

from .codes import ErrorCode
from .tracking import generate_tracking_id

# Keys that must never appear in the sanitized ``context`` dict.
_SENSITIVE_KEYS = frozenset({"password", "secret", "key", "token", "credential"})


class MessageEnvelope(BaseModel):
    """Canonical response shape for all user-facing messages."""

    ok: bool = Field(..., description="True if the operation succeeded")
    category: str = Field(
        ...,
        description="One of: error, warning, status, advice, success, info",
    )
    code: str = Field(..., description="Stable semantic code from ErrorCode enum")
    tracking_id: str = Field(
        ...,
        description="Unique per-event ID (brg-<YYYYMMDDTHHMMSS>-<hex4>)",
    )
    title: str = Field(..., max_length=80, description="Concise human summary")
    message: str = Field(..., description="Plain-English explanation")
    action: str = Field(..., description="Concrete next operator step")
    severity: str = Field(
        ...,
        description="One of: low, medium, high, critical",
    )
    retryable: bool = Field(
        ...,
        description="Whether the same operation can be retried without changes",
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Sanitized technical hints (no credentials)",
    )
    # Legacy backward-compatibility field — populated alongside the envelope
    # so that existing API consumers reading ``detail`` continue to work.
    detail: Any = Field(
        default=None,
        description="Legacy detail field for backward compatibility",
    )
    # Optional: terminal lifecycle state for trade-affecting operations (FR-002)
    operation_state: str | None = Field(
        default=None,
        description="Terminal lifecycle state for trade-affecting operations (accepted, rejected, failed_terminal)",
    )
    # Optional: trade-specific data for success responses
    data: dict[str, Any] | None = Field(
        default=None,
        description="Trade-specific result data (filled_price, ticket_id, etc.)",
    )

    model_config = {"extra": "forbid"}


def _sanitize_context(ctx: dict[str, Any] | None) -> dict[str, Any]:
    """Strip keys that might contain credentials."""
    if not ctx:
        return {}
    return {k: v for k, v in ctx.items() if k.lower() not in _SENSITIVE_KEYS}


class MessageEnvelopeException(HTTPException):
    """HTTPException subclass carrying a pre-built ``MessageEnvelope``.

    Routes raise this instead of plain ``HTTPException`` to produce
    canonical error responses.
    """

    def __init__(
        self,
        *,
        status_code: int | None = None,
        code: ErrorCode,
        message: str | None = None,
        action: str | None = None,
        context: dict[str, Any] | None = None,
        detail: Any = None,
    ) -> None:
        meta = code.value
        resolved_status = status_code if status_code is not None else meta.default_http_status

        self.envelope = MessageEnvelope(
            ok=False,
            category=meta.category,
            code=code.name,
            tracking_id=generate_tracking_id(),
            title=meta.default_title,
            message=message or meta.default_message,
            action=action or meta.default_action,
            severity=meta.default_severity,
            retryable=meta.default_retryable,
            context=_sanitize_context(context),
            detail=detail or (message or meta.default_message),
        )

        # HTTPException stores status_code and detail for compatibility.
        super().__init__(
            status_code=resolved_status,
            detail=self.envelope.detail,
        )
