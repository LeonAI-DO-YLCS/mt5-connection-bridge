from __future__ import annotations

from fastapi import APIRouter

from ..models.worker_info import WorkerInfo
from ..mt5_worker import MAX_RECONNECT_RETRIES, RECONNECT_BASE_DELAY, get_queue_depth, get_state

router = APIRouter(tags=["worker"])


@router.get("/worker/state", response_model=WorkerInfo)
async def worker_state() -> WorkerInfo:
    return WorkerInfo(
        state=get_state().value,
        queue_depth=get_queue_depth(),
        max_reconnect_retries=MAX_RECONNECT_RETRIES,
        reconnect_base_delay=RECONNECT_BASE_DELAY,
    )
