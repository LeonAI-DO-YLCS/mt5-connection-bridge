"""MT5 Bridge — trade request mapping helpers."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from ..models.trade import TradeRequest


def _mt5_const(name: str, default: int) -> int:
    """Resolve an MT5 constant, with safe fallback outside Windows runtime."""
    try:
        import MetaTrader5 as mt5  # type: ignore[import-untyped]

        return int(getattr(mt5, name))
    except Exception:
        return default


def action_to_mt5_order_type(action: str) -> int:
    """Map strategy action to MT5 order type."""
    mapping = {
        "buy": _mt5_const("ORDER_TYPE_BUY", 0),
        "cover": _mt5_const("ORDER_TYPE_BUY", 0),
        "sell": _mt5_const("ORDER_TYPE_SELL", 1),
        "short": _mt5_const("ORDER_TYPE_SELL", 1),
    }
    action_key = action.lower().strip()
    if action_key not in mapping:
        valid = ", ".join(sorted(mapping.keys()))
        raise ValueError(f"Unknown action '{action}'. Valid actions: {valid}")
    return mapping[action_key]


def _precision_from_step(step: float) -> int:
    step_str = f"{step:.10f}".rstrip("0").rstrip(".")
    if "." not in step_str:
        return 0
    return len(step_str.split(".", maxsplit=1)[1])


def normalize_lot_size(quantity: float, symbol_info: Any) -> float:
    """Normalize requested quantity to symbol constraints."""
    if quantity <= 0:
        raise ValueError("quantity must be greater than 0")

    volume_min = float(getattr(symbol_info, "volume_min", 0.0) or 0.0)
    volume_max = float(getattr(symbol_info, "volume_max", quantity) or quantity)
    volume_step = float(getattr(symbol_info, "volume_step", 0.0) or 0.0)

    if volume_step <= 0:
        return max(min(quantity, volume_max), volume_min)

    base = Decimal(str(volume_min))
    q = Decimal(str(quantity))
    step = Decimal(str(volume_step))
    steps = ((q - base) / step).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    normalized = base + (steps * step)
    normalized_float = float(normalized)
    normalized_float = max(normalized_float, volume_min)
    normalized_float = min(normalized_float, volume_max)
    return round(normalized_float, _precision_from_step(volume_step))


def build_order_request(
    trade_req: TradeRequest,
    mt5_symbol: str,
    symbol_info: Any,
) -> dict[str, Any]:
    """Build MT5 `order_send` payload from trade request."""
    trade_action_deal = _mt5_const("TRADE_ACTION_DEAL", 1)
    order_time_gtc = _mt5_const("ORDER_TIME_GTC", 0)
    order_filling_ioc = _mt5_const("ORDER_FILLING_IOC", 2)

    normalized_volume = normalize_lot_size(trade_req.quantity, symbol_info)
    order_type = action_to_mt5_order_type(trade_req.action)
    deviation = int(getattr(symbol_info, "spread", 0) or 0)

    return {
        "action": trade_action_deal,
        "symbol": mt5_symbol,
        "volume": normalized_volume,
        "type": order_type,
        "price": float(trade_req.current_price),
        "deviation": deviation if deviation > 0 else 20,
        "magic": 88001,
        "comment": "ai-hedge-fund mt5 bridge",
        "type_time": order_time_gtc,
        "type_filling": order_filling_ioc,
    }
