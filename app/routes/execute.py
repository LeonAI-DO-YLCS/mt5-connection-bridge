"""MT5 Bridge — POST `/execute` endpoint."""

from __future__ import annotations

import asyncio
import logging
import threading

from fastapi import APIRouter, HTTPException, status

from ..audit import log_trade
from ..main import settings, symbol_map
from ..mappers.trade_mapper import action_to_mt5_order_type, build_order_request, normalize_lot_size
from ..models.trade import TradeRequest, TradeResponse
from ..mt5_worker import WorkerState, get_queue_depth, get_state, submit

logger = logging.getLogger("mt5_bridge.execute")

router = APIRouter(tags=["execution"])

_inflight_lock = threading.Lock()
_inflight_requests = 0


def _safe_pct_delta(a: float, b: float) -> float:
    if b <= 0:
        return 0.0
    return abs(a - b) / b * 100.0


def _acquire_single_flight(req: TradeRequest) -> str | None:
    global _inflight_requests

    with _inflight_lock:
        if not req.multi_trade_mode and _inflight_requests > 0:
            return "Single-flight mode active: wait for current submission to finish or enable multi-trade mode."

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


@router.post("/execute", response_model=TradeResponse)
async def execute_trade(req: TradeRequest) -> TradeResponse:
    if req.ticker not in symbol_map:
        response = TradeResponse(success=False, error=f"Unknown ticker: {req.ticker}")
        log_trade(req, response, metadata={"state": "blocked_unknown_ticker"})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown ticker: {req.ticker}",
        )

    try:
        action_to_mt5_order_type(req.action)
    except ValueError as exc:
        response = TradeResponse(success=False, error=str(exc))
        log_trade(req, response, metadata={"state": "blocked_invalid_action"})
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    if not settings.execution_enabled:
        response = TradeResponse(success=False, error="Execution disabled by policy (EXECUTION_ENABLED=false).")
        log_trade(req, response, metadata={"state": "blocked_execution_disabled"})
        return response

    gate_error = _acquire_single_flight(req)
    if gate_error:
        response = TradeResponse(success=False, error=gate_error)
        log_trade(req, response, metadata={"state": "blocked_overload_or_single_flight"})
        return response

    try:
        if get_state() not in (WorkerState.AUTHORIZED, WorkerState.PROCESSING):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MT5 terminal not connected",
            )

        mt5_symbol = symbol_map[req.ticker].mt5_symbol

        def _execute_in_worker() -> tuple[TradeResponse, str]:
            import MetaTrader5 as mt5  # type: ignore[import-untyped]

            symbol_info = mt5.symbol_info(mt5_symbol)
            if symbol_info is None:
                return TradeResponse(success=False, error=f"Symbol info unavailable for {mt5_symbol}"), "symbol_missing"

            if not symbol_info.visible and not mt5.symbol_select(mt5_symbol, True):
                return (
                    TradeResponse(success=False, error=f"Failed to select symbol {mt5_symbol} in Market Watch"),
                    "symbol_not_selectable",
                )

            tick = mt5.symbol_info_tick(mt5_symbol)
            if tick is not None:
                market_price = float(getattr(tick, "ask", 0.0) or 0.0)
                if req.action in ("sell", "short"):
                    market_price = float(getattr(tick, "bid", market_price) or market_price)
                if market_price > 0:
                    pre_dispatch_delta = _safe_pct_delta(market_price, req.current_price)
                    if pre_dispatch_delta > settings.max_pre_dispatch_slippage_pct:
                        return (
                            TradeResponse(
                                success=False,
                                error=(
                                    "pre_dispatch_slippage_rejection: "
                                    f"delta_pct={pre_dispatch_delta:.4f} exceeds {settings.max_pre_dispatch_slippage_pct:.4f}"
                                ),
                            ),
                            "pre_dispatch_slippage_rejected",
                        )

            try:
                normalized_qty = normalize_lot_size(req.quantity, symbol_info)
            except ValueError as exc:
                return TradeResponse(success=False, error=str(exc)), "invalid_lot"

            order_request = build_order_request(req, mt5_symbol, symbol_info)
            order_request["volume"] = normalized_qty
            logger.info("Submitting MT5 order: %s", order_request)

            result = mt5.order_send(order_request)
            if result is None:
                return TradeResponse(success=False, error=f"order_send returned None: {mt5.last_error()}"), "order_send_none"

            retcode_done = int(getattr(mt5, "TRADE_RETCODE_DONE", 10009))
            if int(getattr(result, "retcode", -1)) != retcode_done:
                return (
                    TradeResponse(
                        success=False,
                        error=(
                            f"Order rejected (retcode={result.retcode}): "
                            f"{getattr(result, 'comment', '')}"
                        ),
                    ),
                    "order_rejected",
                )

            filled_price = float(getattr(result, "price", req.current_price))
            post_fill_delta = _safe_pct_delta(filled_price, req.current_price)
            if post_fill_delta > settings.max_post_fill_slippage_pct:
                return (
                    TradeResponse(
                        success=False,
                        filled_price=filled_price,
                        filled_quantity=float(getattr(result, "volume", normalized_qty)),
                        ticket_id=int(getattr(result, "order", 0) or 0),
                        error=(
                            "post_fill_slippage_exception: "
                            f"delta_pct={post_fill_delta:.4f} exceeds {settings.max_post_fill_slippage_pct:.4f}"
                        ),
                    ),
                    "post_fill_slippage_exception",
                )

            return (
                TradeResponse(
                    success=True,
                    filled_price=filled_price,
                    filled_quantity=float(getattr(result, "volume", normalized_qty)),
                    ticket_id=int(getattr(result, "order", 0) or 0),
                    error=None,
                ),
                "fill_confirmed",
            )

        loop = asyncio.get_running_loop()
        response, trade_state = await asyncio.wrap_future(submit(_execute_in_worker), loop=loop)
        log_trade(req, response, metadata={"state": trade_state})
        logger.info("MT5 order result: %s", response.model_dump())
        return response
    except ConnectionError as exc:
        response = TradeResponse(success=False, error=str(exc))
        log_trade(req, response, metadata={"state": "connection_error"})
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except HTTPException as exc:
        response = TradeResponse(success=False, error=str(exc.detail))
        log_trade(req, response, metadata={"state": "http_error", "status_code": exc.status_code})
        raise
    except Exception as exc:
        response = TradeResponse(success=False, error=str(exc))
        log_trade(req, response, metadata={"state": "internal_error"})
        raise
    finally:
        _release_single_flight()
