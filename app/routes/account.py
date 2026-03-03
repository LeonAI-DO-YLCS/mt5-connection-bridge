from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException

from ..main import settings
from ..mappers.account_mapper import map_mt5_account
from ..models.account import AccountInfo
from ..mt5_worker import submit

router = APIRouter(tags=["account"])

@router.get("/account", response_model=AccountInfo, summary="Get account information")
async def get_account_info():
    """
    Retrieve MT5 account status, metrics, and balance.
    """
    if settings.disable_mt5_worker:
        raise HTTPException(status_code=503, detail="MT5 worker disabled")

    def _get_account_info():
        import MetaTrader5 as mt5  # type: ignore[import-untyped]
        return mt5.account_info()

    try:
        acc_info = await asyncio.wrap_future(submit(_get_account_info))
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Not connected to MT5")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not acc_info:
        raise HTTPException(status_code=503, detail="Failed to retrieve account info")

    return map_mt5_account(acc_info)
