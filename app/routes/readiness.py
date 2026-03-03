"""MT5 Bridge — GET /readiness endpoint (Phase 2).

Returns a structured ``ReadinessResponse`` that aggregates all global
and symbol-specific trade prerequisites.  HTTP 200 always — the readiness
verdict is *data*, not an HTTP error.
"""

from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, Query

from ..messaging.codes import ErrorCode
from ..messaging.envelope import MessageEnvelopeException
from ..models.readiness import ReadinessResponse
from ..services.readiness import evaluate_readiness

logger = logging.getLogger("mt5_bridge.readiness")

router = APIRouter(tags=["readiness"])


@router.get("/readiness", response_model=ReadinessResponse)
async def readiness_check(
    operation: str | None = Query(default=None, description="Trade action type"),
    symbol: str | None = Query(default=None, description="MT5 symbol name"),
    direction: Literal["buy", "sell"] | None = Query(
        default=None, description="Trade direction"
    ),
    volume: float | None = Query(default=None, gt=0, description="Trade volume"),
) -> ReadinessResponse:
    """Evaluate all trade prerequisites and return a structured readiness response."""
    try:
        return await evaluate_readiness(
            operation=operation,
            symbol=symbol,
            direction=direction,
            volume=volume,
        )
    except Exception as exc:
        logger.exception("Readiness evaluation failed: %s", exc)
        raise MessageEnvelopeException(
            code=ErrorCode.READINESS_EVALUATION_FAILED,
            message=f"Readiness evaluation failed: {exc}",
        ) from exc
