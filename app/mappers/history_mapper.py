from datetime import datetime, timezone
from typing import Literal

from ..models.deal import Deal
from ..models.historical_order import HistoricalOrder

DEAL_ENTRY_MAP = {
    0: "in",
    1: "out",
    2: "inout",
    # 3: "out_by" is extremely rare, default to "out" for safety
}

ORDER_STATE_MAP = {
    4: "filled",
    2: "cancelled",
    3: "filled",  # Partial fills are treated as filled
    5: "expired",
    6: "rejected",
    # Others are default stringified
}

def _as_utc_iso(ts: int | float | None) -> str:
    safe_ts = float(ts or 0)
    return datetime.fromtimestamp(safe_ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + "Z"

def map_mt5_deal(deal) -> Deal:
    """
    Map an MT5 deal namedtuple to the Deal Pydantic model.
    """
    return Deal(
        ticket=deal.ticket,
        order_ticket=deal.order,
        position_id=deal.position_id,
        symbol=deal.symbol,
        type="buy" if deal.type == 0 else "sell" if deal.type == 1 else "balance",
        entry=DEAL_ENTRY_MAP.get(deal.entry, "inout"),
        volume=float(deal.volume),
        price=float(deal.price),
        profit=float(deal.profit),
        swap=float(deal.swap),
        commission=float(deal.commission),
        fee=float(deal.fee),
        time=_as_utc_iso(getattr(deal, "time", 0)),
        magic=deal.magic,
    )

def map_mt5_historical_order(ord) -> HistoricalOrder:
    """
    Map an MT5 order from history to the HistoricalOrder Pydantic model.
    """
    volume = getattr(ord, "volume_current", None)
    if volume is None:
        volume = getattr(ord, "volume_initial", getattr(ord, "volume", 0.0))

    time_setup = getattr(ord, "time_setup", 0)
    time_done = getattr(ord, "time_done", None)
    if not time_done:
        time_done = time_setup

    return HistoricalOrder(
        ticket=ord.ticket,
        symbol=ord.symbol,
        type="buy" if ord.type == 0 else "sell" if ord.type == 1 else "pending",
        volume=float(volume),
        price=float(ord.price_open),
        sl=float(ord.sl) if ord.sl > 0.0 else None,
        tp=float(ord.tp) if ord.tp > 0.0 else None,
        state=ORDER_STATE_MAP.get(ord.state, "rejected"), # Default to rejected if unknown state
        time_setup=_as_utc_iso(time_setup),
        time_done=_as_utc_iso(time_done),
        magic=ord.magic,
    )
