from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from ..main import settings, symbol_map
from ..models.config_info import ConfigInfo

router = APIRouter(tags=["config"])


class ExecutionToggleRequest(BaseModel):
    execution_enabled: bool


def _build_config_snapshot() -> ConfigInfo:
    return ConfigInfo(
        mt5_bridge_port=settings.mt5_bridge_port,
        mt5_server=settings.mt5_server,
        mt5_login=settings.mt5_login,
        mt5_path=settings.mt5_path,
        log_level=settings.log_level,
        symbol_count=len(symbol_map),
        symbols_config_path=str(Path(settings.symbols_config_path)),
        execution_enabled=settings.execution_enabled,
        metrics_retention_days=settings.metrics_retention_days,
        multi_trade_overload_queue_threshold=settings.multi_trade_overload_queue_threshold,
    )


@router.get("/config", response_model=ConfigInfo)
async def config_info() -> ConfigInfo:
    return _build_config_snapshot()


@router.put("/config/execution", response_model=ConfigInfo, summary="Toggle execution policy")
async def update_execution_policy(req: ExecutionToggleRequest) -> ConfigInfo:
    settings.execution_enabled = req.execution_enabled
    return _build_config_snapshot()
