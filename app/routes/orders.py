from __future__ import annotations

import asyncio
import threading
from typing import Any, Dict

from fastapi import APIRouter, Header, HTTPException, Path, status

from ..execution.idempotency import compute_request_hash, idempotency_store
from ..execution.lifecycle import OperationState, create_context, transition
from ..execution.observability import emit_operation_log

from ..messaging.codes import ErrorCode
from ..messaging.envelope import MessageEnvelopeException

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
async def cancel_order(
    ticket: int = Path(..., description="Ticket ID of the pending order"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    """
    Cancel an existing pending order by ticket ID.
    """
    request_hash = compute_request_hash({"action": "cancel_order", "ticket": ticket}) if idempotency_key else None
    ctx = create_context("cancel_order", idempotency_key=idempotency_key, request_hash=request_hash)

    if idempotency_key and request_hash:
        cached = idempotency_store.check(idempotency_key, request_hash)
        if cached is not None:
            emit_operation_log(ctx, code="IDEMPOTENCY_KEY_REPLAYED", final_outcome="cache_hit")
            return cached.response
        if idempotency_store.check_conflict(idempotency_key, request_hash):
            raise MessageEnvelopeException(
                code=ErrorCode.IDEMPOTENCY_KEY_CONFLICT,
                message="Idempotency key already used with different parameters.",
            )

    if not settings.execution_enabled:
        transition(ctx, OperationState.REJECTED)
        emit_operation_log(ctx, code="EXECUTION_DISABLED", final_outcome="execution_disabled")
        response = TradeResponse(success=False, error="Execution disabled by policy (EXECUTION_ENABLED=false)")
        log_trade({"action": "cancel_order", "ticket": ticket}, response, metadata={"state": "blocked_execution_disabled"})
        raise MessageEnvelopeException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ErrorCode.EXECUTION_DISABLED,
            message="Execution disabled by policy (EXECUTION_ENABLED=false)",
        )

    if settings.disable_mt5_worker:
        raise HTTPException(status_code=503, detail="MT5 worker disabled")

    gate_error = _acquire_single_flight()
    if gate_error:
        response = TradeResponse(success=False, error=gate_error)
        log_trade({"action": "cancel_order", "ticket": ticket}, response, metadata={"state": "blocked_overload_or_single_flight"})
        raise MessageEnvelopeException(
            status_code=status.HTTP_409_CONFLICT,
            code=ErrorCode.OVERLOAD_OR_SINGLE_FLIGHT,
            message=gate_error,
        )

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
        transition(ctx, OperationState.DISPATCHING)
        response, state = await asyncio.wrap_future(submit(_cancel_order))
        log_trade({"action": "cancel_order", "ticket": ticket}, response, metadata={"state": state})

        if response.success:
            transition(ctx, OperationState.ACCEPTED)
        else:
            transition(ctx, OperationState.REJECTED)
        emit_operation_log(ctx, code="REQUEST_OK" if response.success else "REQUEST_REJECTED", final_outcome=state)

        if idempotency_key and request_hash:
            result_dict = {"success": True, "ticket_id": ticket, "error": None} if response.success else response.model_dump()
            idempotency_store.store(idempotency_key, request_hash, result_dict, "cancel_order")

        if response.success:
            return {"success": True, "ticket_id": ticket, "error": None}
        if state == "order_not_found":
            raise MessageEnvelopeException(
                status_code=status.HTTP_404_NOT_FOUND,
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message=response.error or f"Order {ticket} not found",
                context={"ticket": ticket},
            )
        raise MessageEnvelopeException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.REQUEST_REJECTED,
            message=response.error or "Cancel request failed",
            context={"ticket": ticket},
        )
    except ConnectionError:
        transition(ctx, OperationState.FAILED_TERMINAL)
        emit_operation_log(ctx, code="MT5_DISCONNECTED", final_outcome="connection_error")
        response = TradeResponse(success=False, error="Not connected to MT5")
        log_trade({"action": "cancel_order", "ticket": ticket}, response, metadata={"state": "connection_error"})
        raise MessageEnvelopeException(
            status_code=503,
            code=ErrorCode.MT5_DISCONNECTED,
            message="Not connected to MT5",
        )
    except MessageEnvelopeException:
        raise
    except Exception as e:
        transition(ctx, OperationState.FAILED_TERMINAL)
        emit_operation_log(ctx, code="INTERNAL_SERVER_ERROR", final_outcome="internal_error")
        response = TradeResponse(success=False, error=str(e))
        log_trade({"action": "cancel_order", "ticket": ticket}, response, metadata={"state": "internal_error"})
        raise
    finally:
        _release_single_flight()

@router.put("/orders/{ticket}", summary="Modify a pending order")
async def modify_order(
    req: ModifyOrderRequest,
    ticket: int = Path(..., description="Ticket ID of the pending order"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    """
    Modify an existing pending order.
    """
    request_hash = compute_request_hash({"action": "modify_order", "ticket": ticket, **req.model_dump()}) if idempotency_key else None
    ctx = create_context("modify_order", idempotency_key=idempotency_key, request_hash=request_hash)

    if idempotency_key and request_hash:
        cached = idempotency_store.check(idempotency_key, request_hash)
        if cached is not None:
            emit_operation_log(ctx, code="IDEMPOTENCY_KEY_REPLAYED", final_outcome="cache_hit")
            return cached.response
        if idempotency_store.check_conflict(idempotency_key, request_hash):
            raise MessageEnvelopeException(
                code=ErrorCode.IDEMPOTENCY_KEY_CONFLICT,
                message="Idempotency key already used with different parameters.",
            )

    if not settings.execution_enabled:
        transition(ctx, OperationState.REJECTED)
        emit_operation_log(ctx, code="EXECUTION_DISABLED", final_outcome="execution_disabled")
        response = TradeResponse(success=False, error="Execution disabled by policy (EXECUTION_ENABLED=false)")
        log_trade(
            {"action": "modify_order", "ticket": ticket, "price": req.price, "sl": req.sl, "tp": req.tp},
            response,
            metadata={"state": "blocked_execution_disabled"},
        )
        raise MessageEnvelopeException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ErrorCode.EXECUTION_DISABLED,
            message="Execution disabled by policy (EXECUTION_ENABLED=false)",
        )

    if settings.disable_mt5_worker:
        raise HTTPException(status_code=503, detail="MT5 worker disabled")

    gate_error = _acquire_single_flight()
    if gate_error:
        response = TradeResponse(success=False, error=gate_error)
        log_trade(
            {"action": "modify_order", "ticket": ticket, "price": req.price, "sl": req.sl, "tp": req.tp},
            response,
            metadata={"state": "blocked_overload_or_single_flight"},
        )
        raise MessageEnvelopeException(
            status_code=status.HTTP_409_CONFLICT,
            code=ErrorCode.OVERLOAD_OR_SINGLE_FLIGHT,
            message=gate_error,
        )

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
        transition(ctx, OperationState.DISPATCHING)
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
            transition(ctx, OperationState.ACCEPTED)
        else:
            transition(ctx, OperationState.REJECTED)
        emit_operation_log(ctx, code="REQUEST_OK" if response.success else "REQUEST_REJECTED", final_outcome=state)

        if idempotency_key and request_hash:
            result_dict = {"success": True, "ticket_id": ticket, "error": None} if response.success else response.model_dump()
            idempotency_store.store(idempotency_key, request_hash, result_dict, "modify_order")

        if response.success:
            return {"success": True, "ticket_id": ticket, "error": None}
        if state == "order_not_found":
            raise MessageEnvelopeException(
                status_code=status.HTTP_404_NOT_FOUND,
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message=response.error or f"Order {ticket} not found",
                context={"ticket": ticket},
            )
        raise MessageEnvelopeException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.REQUEST_REJECTED,
            message=response.error or "Modify request failed",
            context={"ticket": ticket},
        )
    except ConnectionError:
        transition(ctx, OperationState.FAILED_TERMINAL)
        emit_operation_log(ctx, code="MT5_DISCONNECTED", final_outcome="connection_error")
        response = TradeResponse(success=False, error="Not connected to MT5")
        log_trade(
            {"action": "modify_order", "ticket": ticket, "price": req.price, "sl": req.sl, "tp": req.tp},
            response,
            metadata={"state": "connection_error"},
        )
        raise MessageEnvelopeException(
            status_code=503,
            code=ErrorCode.MT5_DISCONNECTED,
            message="Not connected to MT5",
        )
    except MessageEnvelopeException:
        raise
    except Exception as e:
        transition(ctx, OperationState.FAILED_TERMINAL)
        emit_operation_log(ctx, code="INTERNAL_SERVER_ERROR", final_outcome="internal_error")
        response = TradeResponse(success=False, error=str(e))
        log_trade(
            {"action": "modify_order", "ticket": ticket, "price": req.price, "sl": req.sl, "tp": req.tp},
            response,
            metadata={"state": "internal_error"},
        )
        raise
    finally:
        _release_single_flight()
