from __future__ import annotations

import asyncio
import threading
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Path, status

from ..audit import log_trade
from ..main import settings
from ..mappers.position_mapper import map_mt5_position
from ..models.modify_sltp import ModifySLTPRequest
from ..models.trade import TradeResponse
from ..mt5_worker import get_queue_depth, submit

router = APIRouter(tags=["positions"])

_inflight_lock = threading.Lock()
_inflight_requests = 0


def _acquire_single_flight() -> str | None:
    global _inflight_requests
    with _inflight_lock:
        if _inflight_requests > 0:
            return "Single-flight mode active: wait for current submission to finish."
        pending = _inflight_requests + get_queue_depth()
        if pending >= settings.multi_trade_overload_queue_threshold:
            return (
                "Execution queue overload protection triggered. "
                f"Pending={pending}, threshold={settings.multi_trade_overload_queue_threshold}."
            )
        _inflight_requests += 1
    return None


def _release_single_flight() -> None:
    global _inflight_requests
    with _inflight_lock:
        _inflight_requests = max(_inflight_requests - 1, 0)

@router.get("/positions", summary="Get all open positions")
async def get_positions() -> Dict[str, Any]:
    """
    Retrieve all currently open positions.
    """
    if settings.disable_mt5_worker:
        raise HTTPException(status_code=503, detail="MT5 worker disabled")

    def _get_positions():
        import MetaTrader5 as mt5  # type: ignore[import-untyped]
        return mt5.positions_get()

    try:
        positions_data = await asyncio.wrap_future(submit(_get_positions))
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Not connected to MT5")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if positions_data is None:
        return {"positions": [], "count": 0}

    mapped_positions = [map_mt5_position(p) for p in positions_data]
    return {"positions": mapped_positions, "count": len(mapped_positions)}

@router.put("/positions/{ticket}/sltp", summary="Modify Stop Loss and Take Profit")
async def modify_sltp(req: ModifySLTPRequest, ticket: int = Path(..., description="Ticket ID of the open position")):
    """
    Modify Stop Loss and/or Take Profit for an open position.
    """
    if not settings.execution_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Execution disabled by policy (EXECUTION_ENABLED=false)"
        )

    if settings.disable_mt5_worker:
        raise HTTPException(status_code=503, detail="MT5 worker disabled")

    gate_error = _acquire_single_flight()
    if gate_error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=gate_error)

    def _modify_sltp():
        from ..mappers.trade_mapper import build_modify_sltp_request
        import MetaTrader5 as mt5  # type: ignore[import-untyped]
        
        request = build_modify_sltp_request(ticket, req.sl, req.tp)
        result = mt5.order_send(request)
        if result is None:
            return TradeResponse(success=False, error=f"order_send failed: {mt5.last_error()}"), "order_send_none"
        
        retcode_done = int(getattr(mt5, "TRADE_RETCODE_DONE", 10009))
        if int(getattr(result, "retcode", -1)) != retcode_done:
            error = f"Order rejected (retcode={result.retcode}): {getattr(result, 'comment', '')}"
            state = "position_not_found" if "not found" in error.lower() else "order_rejected"
            return TradeResponse(success=False, error=error), state

        return TradeResponse(success=True, ticket_id=ticket, error=None), "modified"

    try:
        response, state = await asyncio.wrap_future(submit(_modify_sltp))
        log_trade(
            {"action": "modify_sltp", "ticket": ticket, "sl": req.sl, "tp": req.tp},
            response,
            metadata={"state": state},
        )
        if response.success:
            return {"success": True, "ticket_id": ticket, "error": None}
        if state == "position_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=response.error)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.error)
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Not connected to MT5")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        _release_single_flight()
