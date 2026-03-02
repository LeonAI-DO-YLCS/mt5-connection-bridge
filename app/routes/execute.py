"""MT5 Bridge — POST `/execute` endpoint."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException, status

from ..audit import log_trade
from ..main import symbol_map
from ..mappers.trade_mapper import (
    action_to_mt5_order_type,
    build_order_request,
    normalize_lot_size,
)
from ..models.trade import TradeRequest, TradeResponse
from ..mt5_worker import WorkerState, get_state, submit

logger = logging.getLogger("mt5_bridge.execute")

router = APIRouter(tags=["execution"])


@router.post("/execute", response_model=TradeResponse)
async def execute_trade(req: TradeRequest) -> TradeResponse:
    """Execute a live trade via MT5 and return fill details."""
    if req.ticker not in symbol_map:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown ticker: {req.ticker}",
        )

    try:
        action_to_mt5_order_type(req.action)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    if get_state() not in (WorkerState.AUTHORIZED, WorkerState.PROCESSING):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MT5 terminal not connected",
        )

    mt5_symbol = symbol_map[req.ticker].mt5_symbol

    def _execute_in_worker() -> TradeResponse:
        import MetaTrader5 as mt5  # type: ignore[import-untyped]

        symbol_info = mt5.symbol_info(mt5_symbol)
        if symbol_info is None:
            return TradeResponse(
                success=False,
                error=f"Symbol info unavailable for {mt5_symbol}",
            )

        if not symbol_info.visible and not mt5.symbol_select(mt5_symbol, True):
            return TradeResponse(
                success=False,
                error=f"Failed to select symbol {mt5_symbol} in Market Watch",
            )

        try:
            normalized_qty = normalize_lot_size(req.quantity, symbol_info)
        except ValueError as exc:
            return TradeResponse(success=False, error=str(exc))

        order_request = build_order_request(req, mt5_symbol, symbol_info)
        order_request["volume"] = normalized_qty
        logger.info("Submitting MT5 order: %s", order_request)

        result = mt5.order_send(order_request)
        if result is None:
            return TradeResponse(
                success=False,
                error=f"order_send returned None: {mt5.last_error()}",
            )

        retcode_done = int(getattr(mt5, "TRADE_RETCODE_DONE", 10009))
        if int(getattr(result, "retcode", -1)) != retcode_done:
            return TradeResponse(
                success=False,
                error=f"Order rejected (retcode={result.retcode}): {getattr(result, 'comment', '')}",
            )

        return TradeResponse(
            success=True,
            filled_price=float(getattr(result, "price", req.current_price)),
            filled_quantity=float(getattr(result, "volume", normalized_qty)),
            ticket_id=int(getattr(result, "order", 0)),
            error=None,
        )

    try:
        loop = asyncio.get_running_loop()
        response = await asyncio.wrap_future(submit(_execute_in_worker), loop=loop)
    except ConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    log_trade(req, response)
    logger.info("MT5 order result: %s", response.model_dump())
    return response
