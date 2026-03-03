from datetime import datetime, timezone


from ..models.order import Order
from .trade_mapper import _mt5_const

ORDER_TYPE_MAP = {
    _mt5_const("ORDER_TYPE_BUY_LIMIT", 2): "buy_limit",
    _mt5_const("ORDER_TYPE_SELL_LIMIT", 3): "sell_limit",
    _mt5_const("ORDER_TYPE_BUY_STOP", 4): "buy_stop",
    _mt5_const("ORDER_TYPE_SELL_STOP", 5): "sell_stop",
}

def pending_type_to_mt5_const(type_str: str) -> int:
    """
    Convert a string pending type to the MT5 constant value.
    """
    const_name = f"ORDER_TYPE_{type_str.upper()}"
    defaults = {
        "buy_limit": 2,
        "sell_limit": 3,
        "buy_stop": 4,
        "sell_stop": 5
    }
    return _mt5_const(const_name, defaults.get(type_str, -1))

def map_mt5_order(ord) -> Order:
    """
    Map an MT5 order namedtuple to the Order Pydantic model.
    """
    return Order(
        ticket=ord.ticket,
        symbol=ord.symbol,
        type=ORDER_TYPE_MAP.get(ord.type, "unknown"),
        volume=float(ord.volume_initial),  # Use volume_initial for pending orders
        price=float(ord.price_open),
        sl=float(ord.sl) if ord.sl > 0.0 else None,
        tp=float(ord.tp) if ord.tp > 0.0 else None,
        time_setup=datetime.fromtimestamp(ord.time_setup, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + "Z",
        magic=ord.magic,
    )
