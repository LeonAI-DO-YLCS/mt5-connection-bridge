from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException

from ..main import settings
from ..models.terminal import TerminalInfo
from ..mt5_worker import submit

router = APIRouter(tags=["terminal"])

@router.get("/terminal", response_model=TerminalInfo, summary="Get terminal information")
async def get_terminal_info():
    """
    Retrieve MT5 terminal build info, connection status, and path detail.
    """
    if settings.disable_mt5_worker:
        raise HTTPException(status_code=503, detail="MT5 worker disabled")

    def _get_terminal_info():
        import MetaTrader5 as mt5  # type: ignore[import-untyped]
        return mt5.terminal_info()

    try:
        term_info = await asyncio.wrap_future(submit(_get_terminal_info))
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Not connected to MT5")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not term_info:
        raise HTTPException(status_code=503, detail="Failed to retrieve terminal info")

    return TerminalInfo(
        build=term_info.build,
        name=term_info.name,
        path=term_info.path,
        data_path=term_info.data_path,
        connected=term_info.connected,
        trade_allowed=term_info.trade_allowed
    )
