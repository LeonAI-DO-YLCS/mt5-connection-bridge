from __future__ import annotations

import asyncio
import threading
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Path, status

from ..audit import log_trade
from ..main import settings
from ..mappers.order_mapper import map_mt5_order
from ..models.modify_order import ModifyOrderRequest
from ..models.trade import TradeResponse
from ..mt5_worker import get_queue_depth, submit

router = APIRouter(tags=["orders"])

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

@router.get("/orders", summary="Get all pending orders")
async def get_orders() -> Dict[str, Any]:
    """
    Retrieve all currently open pending orders.
    """
    if settings.disable_mt5_worker:
        raise HTTPException(status_code=503, detail="MT5 worker disabled")

    def _get_orders():
        import MetaTrader5 as mt5  # type: ignore[import-untyped]
        return mt5.orders_get()

    try:
        orders_data = await asyncio.wrap_future(submit(_get_orders))
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Not connected to MT5")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if orders_data is None:
        return {"orders": [], "count": 0}

    mapped_orders = [map_mt5_order(o) for o in orders_data]
    return {"orders": mapped_orders, "count": len(mapped_orders)}

@router.delete("/orders/{ticket}", summary="Cancel a pending order")
async def cancel_order(ticket: int = Path(..., description="Ticket ID of the pending order")):
    """
    Cancel an existing pending order by ticket ID.
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

    def _cancel_order():
        from ..mappers.trade_mapper import build_cancel_order_request
        import MetaTrader5 as mt5  # type: ignore[import-untyped]
        
        request = build_cancel_order_request(ticket)
        result = mt5.order_send(request)
        if result is None:
            return TradeResponse(success=False, error=f"order_send failed: {mt5.last_error()}"), "order_send_none"
        
        retcode_done = int(getattr(mt5, "TRADE_RETCODE_DONE", 10009))
        if int(getattr(result, "retcode", -1)) != retcode_done:
            error = f"Order rejected (retcode={result.retcode}): {getattr(result, 'comment', '')}"
            state = "order_not_found" if "not found" in error.lower() else "order_rejected"
            return TradeResponse(success=False, error=error), state

        return TradeResponse(success=True, ticket_id=ticket, error=None), "cancelled"

    try:
        response, state = await asyncio.wrap_future(submit(_cancel_order))
        log_trade({"action": "cancel_order", "ticket": ticket}, response, metadata={"state": state})
        if response.success:
            return {"success": True, "ticket_id": ticket, "error": None}
        if state == "order_not_found":
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

@router.put("/orders/{ticket}", summary="Modify a pending order")
async def modify_order(req: ModifyOrderRequest, ticket: int = Path(..., description="Ticket ID of the pending order")):
    """
    Modify an existing pending order.
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

    def _modify_order():
        from ..mappers.trade_mapper import build_modify_order_request
        import MetaTrader5 as mt5  # type: ignore[import-untyped]
        
        request = build_modify_order_request(ticket, req.price, req.sl, req.tp)
        result = mt5.order_send(request)
        if result is None:
            return TradeResponse(success=False, error=f"order_send failed: {mt5.last_error()}"), "order_send_none"
        
        retcode_done = int(getattr(mt5, "TRADE_RETCODE_DONE", 10009))
        if int(getattr(result, "retcode", -1)) != retcode_done:
            error = f"Order rejected (retcode={result.retcode}): {getattr(result, 'comment', '')}"
            state = "order_not_found" if "not found" in error.lower() else "order_rejected"
            return TradeResponse(success=False, error=error), state

        return TradeResponse(success=True, ticket_id=ticket, error=None), "modified"

    try:
        response, state = await asyncio.wrap_future(submit(_modify_order))
        log_trade(
            {
                "action": "modify_order",
                "ticket": ticket,
                "price": req.price,
                "sl": req.sl,
                "tp": req.tp,
            },
            response,
            metadata={"state": state},
        )
        if response.success:
            return {"success": True, "ticket_id": ticket, "error": None}
        if state == "order_not_found":
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
