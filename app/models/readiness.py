"""MT5 Bridge — Readiness response models (Phase 2).

Defines the structured response for ``GET /readiness``, which aggregates
all global and symbol-specific trade prerequisites into a single payload.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ReadinessStatus(str, Enum):
    """Status of an individual readiness check."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    UNKNOWN = "unknown"


class OverallStatus(str, Enum):
    """Aggregate readiness verdict derived from the checks array."""

    READY = "ready"
    DEGRADED = "degraded"
    BLOCKED = "blocked"


class ReadinessCheck(BaseModel):
    """A single evaluated pre-condition."""

    check_id: str = Field(
        ...,
        description="Stable dotted identifier, e.g. 'global.worker_connected'",
    )
    status: ReadinessStatus = Field(
        ...,
        description="Result of the check: pass, warn, fail, or unknown",
    )
    blocking: bool = Field(
        ...,
        description="True if this check prevents the operation from proceeding",
    )
    user_message: str = Field(
        ...,
        description="Plain-English explanation suitable for non-technical operators",
    )
    action: str = Field(
        ...,
        description="Concrete next step to resolve the issue (empty string when status=pass)",
    )
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Technical details for support engineers (raw values, thresholds, etc.)",
    )


class ReadinessRequestContext(BaseModel):
    """Echo of query parameters used to scope the readiness evaluation."""

    operation: str | None = Field(default=None, description="Trade action type")
    symbol: str | None = Field(default=None, description="MT5 symbol name or alias")
    direction: str | None = Field(default=None, description="buy or sell")
    volume: float | None = Field(default=None, description="Requested trade volume")


class ReadinessResponse(BaseModel):
    """Structured readiness evaluation result for ``GET /readiness``."""

    overall_status: OverallStatus = Field(
        ...,
        description="Aggregate verdict: ready, degraded, or blocked",
    )
    checks: list[ReadinessCheck] = Field(
        ...,
        description="Full list of evaluated checks in evaluation order",
    )
    blockers: list[ReadinessCheck] = Field(
        ...,
        description="Subset: all checks with status=fail AND blocking=true",
    )
    warnings: list[ReadinessCheck] = Field(
        ...,
        description="Subset: all checks with status=warn",
    )
    advice: list[ReadinessCheck] = Field(
        ...,
        description="Subset: informational items",
    )
    evaluated_at: str = Field(
        ...,
        description="ISO-8601 UTC timestamp of evaluation",
    )
    request_context: ReadinessRequestContext = Field(
        ...,
        description="Echo of the parameters used to scope this evaluation",
    )
