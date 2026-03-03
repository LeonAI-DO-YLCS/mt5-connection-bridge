"""MT5 Bridge — Canonical error code taxonomy.

Each ErrorCode member carries its default metadata so that the normalizer
can construct a complete MessageEnvelope from just the code + a context-specific message.
"""

from __future__ import annotations

from enum import Enum
from typing import NamedTuple


class _CodeMeta(NamedTuple):
    """Metadata bundle for an error code."""

    domain: str
    default_title: str
    default_message: str
    default_action: str
    default_severity: str
    default_retryable: bool
    default_http_status: int
    category: str


class ErrorCode(Enum):
    """Canonical error codes for the MT5 Bridge messaging system.

    Each member's ``value`` is an ``_CodeMeta`` namedtuple containing
    the default envelope fields for that code.
    """

    # ── Success ──────────────────────────────────────────────────────────
    REQUEST_OK = _CodeMeta(
        domain="REQUEST",
        default_title="Operation completed successfully",
        default_message="The operation completed without errors.",
        default_action="No action required.",
        default_severity="low",
        default_retryable=False,
        default_http_status=200,
        category="success",
    )

    # ── Validation domain ────────────────────────────────────────────────
    VALIDATION_VOLUME_RANGE = _CodeMeta(
        domain="VALIDATION",
        default_title="Invalid trade volume",
        default_message="The requested volume is outside the allowed range for this symbol.",
        default_action="Adjust the volume to be within the symbol's allowed range.",
        default_severity="medium",
        default_retryable=False,
        default_http_status=422,
        category="error",
    )
    VALIDATION_VOLUME_STEP = _CodeMeta(
        domain="VALIDATION",
        default_title="Invalid volume step",
        default_message="The requested volume does not align with the symbol's step size.",
        default_action="Round the volume to the nearest valid step size.",
        default_severity="medium",
        default_retryable=False,
        default_http_status=422,
        category="error",
    )
    VALIDATION_CURRENT_PRICE_GT_ZERO = _CodeMeta(
        domain="VALIDATION",
        default_title="Price must be positive",
        default_message="The current price must be greater than zero.",
        default_action="Provide a current price greater than zero.",
        default_severity="medium",
        default_retryable=False,
        default_http_status=422,
        category="error",
    )
    VALIDATION_ERROR = _CodeMeta(
        domain="VALIDATION",
        default_title="Input validation failed",
        default_message="One or more input fields did not pass validation.",
        default_action="Check the highlighted fields and correct the input.",
        default_severity="medium",
        default_retryable=False,
        default_http_status=422,
        category="error",
    )

    # ── Connectivity / runtime domain ────────────────────────────────────
    MT5_DISCONNECTED = _CodeMeta(
        domain="MT5",
        default_title="MT5 terminal disconnected",
        default_message="The connection to the MetaTrader 5 terminal has been lost.",
        default_action="Wait for automatic reconnect, then retry.",
        default_severity="critical",
        default_retryable=True,
        default_http_status=503,
        category="error",
    )
    MT5_RUNTIME_UNAVAILABLE = _CodeMeta(
        domain="MT5",
        default_title="MT5 runtime unavailable",
        default_message="The MetaTrader 5 runtime is not responding.",
        default_action="Check that the MetaTrader 5 terminal is running.",
        default_severity="critical",
        default_retryable=True,
        default_http_status=503,
        category="error",
    )
    WORKER_RECONNECT_EXHAUSTED = _CodeMeta(
        domain="WORKER",
        default_title="Reconnection failed",
        default_message="All reconnection attempts to the MT5 terminal have been exhausted.",
        default_action="Restart the bridge manually.",
        default_severity="critical",
        default_retryable=False,
        default_http_status=503,
        category="error",
    )
    SERVICE_UNAVAILABLE = _CodeMeta(
        domain="MT5",
        default_title="Service temporarily unavailable",
        default_message="The service is temporarily unavailable.",
        default_action="Wait a moment and retry the operation.",
        default_severity="critical",
        default_retryable=True,
        default_http_status=503,
        category="error",
    )

    # ── Policy / capability domain ───────────────────────────────────────
    EXECUTION_DISABLED = _CodeMeta(
        domain="EXECUTION",
        default_title="Execution disabled by policy",
        default_message="Trade execution is currently disabled by the bridge configuration.",
        default_action="Enable execution via environment config or the dashboard toggle.",
        default_severity="high",
        default_retryable=False,
        default_http_status=403,
        category="error",
    )
    SYMBOL_TRADE_MODE_RESTRICTED = _CodeMeta(
        domain="SYMBOL",
        default_title="Symbol trade mode restricted",
        default_message="The requested trade action is not allowed for this symbol's current trade mode.",
        default_action="Select a different action or choose a symbol that allows this trade type.",
        default_severity="high",
        default_retryable=False,
        default_http_status=422,
        category="error",
    )
    SYMBOL_NOT_CONFIGURED = _CodeMeta(
        domain="SYMBOL",
        default_title="Symbol not configured",
        default_message="The requested symbol is not configured in the bridge's symbol map.",
        default_action="Add the symbol to symbols.yaml or use the direct symbol field.",
        default_severity="high",
        default_retryable=False,
        default_http_status=404,
        category="error",
    )
    FILLING_MODE_UNSUPPORTED = _CodeMeta(
        domain="SYMBOL",
        default_title="Filling mode not supported",
        default_message="The symbol's broker does not support the required filling mode.",
        default_action="Contact support with the tracking ID.",
        default_severity="high",
        default_retryable=False,
        default_http_status=422,
        category="error",
    )

    # ── Request compatibility domain ─────────────────────────────────────
    REQUEST_REJECTED = _CodeMeta(
        domain="REQUEST",
        default_title="Trade request rejected",
        default_message="The trade request was rejected by the broker.",
        default_action="Review the order parameters and try again.",
        default_severity="high",
        default_retryable=False,
        default_http_status=400,
        category="error",
    )
    OVERLOAD_OR_SINGLE_FLIGHT = _CodeMeta(
        domain="REQUEST",
        default_title="Execution queue busy",
        default_message="The execution queue is currently processing another request.",
        default_action="Wait for the current trade to complete, then retry.",
        default_severity="medium",
        default_retryable=True,
        default_http_status=409,
        category="warning",
    )
    RESOURCE_NOT_FOUND = _CodeMeta(
        domain="REQUEST",
        default_title="Resource not found",
        default_message="The requested resource could not be found.",
        default_action="Verify the ticket or resource identifier.",
        default_severity="medium",
        default_retryable=False,
        default_http_status=404,
        category="error",
    )
    REQUEST_ERROR = _CodeMeta(
        domain="REQUEST",
        default_title="Request error",
        default_message="The request could not be processed.",
        default_action="Review the request and try again.",
        default_severity="medium",
        default_retryable=False,
        default_http_status=400,
        category="error",
    )

    # ── Generic / internal domain ────────────────────────────────────────
    INTERNAL_SERVER_ERROR = _CodeMeta(
        domain="INTERNAL",
        default_title="Internal server error",
        default_message="An unexpected error occurred within the bridge.",
        default_action="Contact support with the tracking ID shown above.",
        default_severity="critical",
        default_retryable=True,
        default_http_status=500,
        category="error",
    )
    UNAUTHORIZED_API_KEY = _CodeMeta(
        domain="INTERNAL",
        default_title="Authentication required",
        default_message="A valid API key is required to access this endpoint.",
        default_action="Provide a valid API key in the request header.",
        default_severity="high",
        default_retryable=False,
        default_http_status=401,
        category="error",
    )

    # ── Convenience accessors ────────────────────────────────────────────

    @property
    def domain(self) -> str:
        return self.value.domain

    @property
    def default_title(self) -> str:
        return self.value.default_title

    @property
    def default_message(self) -> str:
        return self.value.default_message

    @property
    def default_action(self) -> str:
        return self.value.default_action

    @property
    def default_severity(self) -> str:
        return self.value.default_severity

    @property
    def default_retryable(self) -> bool:
        return self.value.default_retryable

    @property
    def default_http_status(self) -> int:
        return self.value.default_http_status

    @property
    def default_category(self) -> str:
        return self.value.category
