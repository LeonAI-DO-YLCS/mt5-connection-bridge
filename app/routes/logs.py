from __future__ import annotations

from fastapi import APIRouter, Query

from ..audit import read_trade_logs
from ..models.log_entry import LogsResponse

router = APIRouter(tags=["logs"])


@router.get("/logs", response_model=LogsResponse)
async def get_logs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> LogsResponse:
    return read_trade_logs(limit=limit, offset=offset)
