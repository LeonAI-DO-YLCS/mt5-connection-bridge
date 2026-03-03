import asyncio
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from ..mappers.history_mapper import map_mt5_deal, map_mt5_historical_order
from ..models.deal import Deal
from ..models.historical_order import HistoricalOrder
from ..mt5_worker import WorkerState, get_state, submit

router = APIRouter(prefix="/history", tags=["History"])

class DealsResponse(BaseModel):
    deals: List[Deal]
    count: int
    net_profit: float
    total_swap: float
    total_commission: float

class OrdersResponse(BaseModel):
    orders: List[HistoricalOrder]
    count: int

def parse_iso_to_datetime(dt_str: str) -> datetime:
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {dt_str}. Expected ISO 8601.")

@router.get("/deals", response_model=DealsResponse, summary="Get historical deals")
async def get_deals(
    date_from: str = Query(..., description="Start date in ISO 8601 format"),
    date_to: str = Query(..., description="End date in ISO 8601 format"),
    symbol: Optional[str] = Query(None, description="Filter by instrument symbol"),
    position: Optional[int] = Query(None, description="Filter by position ID")
) -> DealsResponse:
    
    dt_from = parse_iso_to_datetime(date_from)
    dt_to = parse_iso_to_datetime(date_to)

    if get_state() not in (WorkerState.AUTHORIZED, WorkerState.PROCESSING):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MT5 terminal not connected",
        )

    def _fetch_deals() -> DealsResponse:
        import MetaTrader5 as mt5 # type: ignore[import-untyped]
        
        deals_mt5 = mt5.history_deals_get(dt_from, dt_to)
        
        if deals_mt5 is None:
            err = mt5.last_error()
            if err[0] == 1: # MT_RET_OK, just empty
                return DealsResponse(deals=[], count=0, net_profit=0.0, total_swap=0.0, total_commission=0.0)
            raise Exception(f"Failed to fetch deals: {err}")
        
        deals: List[Deal] = []
        net_profit = 0.0
        total_swap = 0.0
        total_commission = 0.0
        
        for d in deals_mt5:
            if symbol and getattr(d, 'symbol', '') != symbol:
                continue
            if position is not None and getattr(d, 'position_id', -1) != position:
                continue
                
            mapped = map_mt5_deal(d)
            deals.append(mapped)
            
            net_profit += mapped.profit
            total_swap += mapped.swap
            total_commission += mapped.commission + mapped.fee

        return DealsResponse(
            deals=deals,
            count=len(deals),
            net_profit=round(net_profit, 5),
            total_swap=round(total_swap, 5),
            total_commission=round(total_commission, 5)
        )

    loop = asyncio.get_running_loop()
    try:
        return await asyncio.wrap_future(submit(_fetch_deals), loop=loop)
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Not connected to MT5")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders", response_model=OrdersResponse, summary="Get historical orders")
async def get_orders(
    date_from: str = Query(..., description="Start date in ISO 8601 format"),
    date_to: str = Query(..., description="End date in ISO 8601 format"),
    symbol: Optional[str] = Query(None, description="Filter by instrument symbol")
) -> OrdersResponse:
    
    dt_from = parse_iso_to_datetime(date_from)
    dt_to = parse_iso_to_datetime(date_to)

    if get_state() not in (WorkerState.AUTHORIZED, WorkerState.PROCESSING):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MT5 terminal not connected",
        )

    def _fetch_orders() -> OrdersResponse:
        import MetaTrader5 as mt5 # type: ignore[import-untyped]
        
        orders_mt5 = mt5.history_orders_get(dt_from, dt_to)
        
        if orders_mt5 is None:
            err = mt5.last_error()
            if err[0] == 1:
                return OrdersResponse(orders=[], count=0)
            raise Exception(f"Failed to fetch orders: {err}")
            
        orders: List[HistoricalOrder] = []
        
        for o in orders_mt5:
            if symbol and getattr(o, 'symbol', '') != symbol:
                continue
            orders.append(map_mt5_historical_order(o))

        return OrdersResponse(
            orders=orders,
            count=len(orders)
        )

    loop = asyncio.get_running_loop()
    try:
        return await asyncio.wrap_future(submit(_fetch_orders), loop=loop)
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Not connected to MT5")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
