"""MT5 Bridge — trade request mapping helpers."""

from __future__ import annotations

import logging
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from ..models.pending_order import PendingOrderRequest
from ..models.trade import TradeRequest
from ..execution.comment import CommentNormalizer

_comment_normalizer = CommentNormalizer()

logger = logging.getLogger("mt5_bridge.trade_mapper")

# Actions that initiate a LONG (buy-direction) position
_BUY_ACTIONS = {"buy", "cover", "buy_limit", "buy_stop"}
# Actions that initiate a SHORT (sell-direction) position
_SELL_ACTIONS = {"sell", "short", "sell_limit", "sell_stop"}


def _mt5_const(name: str, default: int) -> int:
    """Resolve an MT5 constant, with safe fallback outside Windows runtime."""
    try:
        import MetaTrader5 as mt5  # type: ignore[import-untyped]

        return int(getattr(mt5, name))
    except Exception:
        return default


def resolve_filling_mode(symbol_info: Any) -> int:
    """Dynamically select the best supported filling mode for a symbol.

    Reads ``symbol_info.filling_mode`` as a bitmask:
      - bit 0 (value 1) → ORDER_FILLING_FOK supported
      - bit 1 (value 2) → ORDER_FILLING_IOC supported
      - neither bit set → ORDER_FILLING_RETURN (always-safe fallback)

    Priority: FOK > IOC > RETURN.
    """
    bitmask = int(getattr(symbol_info, "filling_mode", 0) or 0)
    fok = _mt5_const("ORDER_FILLING_FOK", 1)
    ioc = _mt5_const("ORDER_FILLING_IOC", 2)
    ret = _mt5_const("ORDER_FILLING_RETURN", 0)

    if bitmask & 1:
        return fok
    if bitmask & 2:
        return ioc
    return ret


def validate_trade_mode(symbol_info: Any, action: str) -> str | None:
    """Validate that the requested action is allowed by the symbol's trade mode.

    Returns an error string if the action is prohibited, or ``None`` if allowed.
    Treats unknown ``trade_mode`` values as FULL (allow all) and logs a warning.

    Trade mode values:
      0 = DISABLED   — no trades at all
      1 = LONG ONLY  — only buy-direction orders allowed
      2 = SHORT ONLY — only sell-direction orders allowed
      3 = CLOSE ONLY — no new positions; only close existing
      4 = FULL       — all operations allowed
    """
    raw = getattr(symbol_info, "trade_mode", 4)
    try:
        trade_mode = int(raw)
    except (TypeError, ValueError):
        trade_mode = 4

    symbol_name = getattr(symbol_info, "name", "this symbol")
    action_lower = action.lower().strip()

    if trade_mode == 0:
        return f"Symbol {symbol_name} trading is currently disabled by the broker."

    if trade_mode == 1 and action_lower in _SELL_ACTIONS:
        return (
            f"Symbol {symbol_name} only allows long (buy) trades. "
            "Sell orders are not permitted."
        )

    if trade_mode == 2 and action_lower in _BUY_ACTIONS:
        return (
            f"Symbol {symbol_name} only allows short (sell) trades. "
            "Buy orders are not permitted."
        )

    if trade_mode == 3:
        return (
            f"Symbol {symbol_name} is in close-only mode. "
            "No new positions are allowed by the broker."
        )

    if trade_mode not in (0, 1, 2, 3, 4):
        logger.warning(
            "Unknown trade_mode=%s for symbol %s — treating as FULL (allow all).",
            raw,
            symbol_name,
        )

    return None


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
    """Build MT5 ``order_send`` payload from trade request."""
    trade_action_deal = _mt5_const("TRADE_ACTION_DEAL", 1)
    order_time_gtc = _mt5_const("ORDER_TIME_GTC", 0)

    normalized_volume = normalize_lot_size(trade_req.quantity, symbol_info)
    order_type = action_to_mt5_order_type(trade_req.action)
    deviation = int(getattr(symbol_info, "spread", 0) or 0)

    return {
        "action": trade_action_deal,
        "symbol": mt5_symbol,
        "volume": normalized_volume,
        "type": order_type,
        "price": float(trade_req.current_price),
        "sl": float(trade_req.sl) if trade_req.sl else 0.0,
        "tp": float(trade_req.tp) if trade_req.tp else 0.0,
        "deviation": deviation if deviation > 0 else 20,
        "magic": 88001,
        "comment": _comment_normalizer.normalize("ai-hedge-fund mt5 bridge"),
        "type_time": order_time_gtc,
        "type_filling": resolve_filling_mode(symbol_info),  # T005–T007: dynamic resolution
    }


def build_close_request(position: Any, volume: float | None, symbol_info: Any) -> dict[str, Any]:
    """Build MT5 ``order_send`` payload for closing a position."""
    trade_action_deal = _mt5_const("TRADE_ACTION_DEAL", 1)

    # Counter-order type
    order_type_sell = _mt5_const("ORDER_TYPE_SELL", 1)
    order_type_buy = _mt5_const("ORDER_TYPE_BUY", 0)

    # MT5 position.type is 0 for BUY, 1 for SELL
    if position.type == 0:  # Buy position → counter with Sell
        counter_type = order_type_sell
    else:
        counter_type = order_type_buy

    vol_to_close = float(volume) if volume is not None else float(position.volume)
    # For explicit partial close requests, keep the caller volume unchanged after validation.
    # Full-close requests still normalize to symbol constraints.
    normalized_volume = vol_to_close if volume is not None else normalize_lot_size(vol_to_close, symbol_info)

    return {
        "action": trade_action_deal,
        "symbol": position.symbol,
        "volume": normalized_volume,
        "type": counter_type,
        "position": position.ticket,
        "magic": 88001,
        "comment": _comment_normalizer.normalize("ai-hedge-fund mt5 bridge close"),
        "type_filling": resolve_filling_mode(symbol_info),  # T010: dynamic filling mode for close
    }


def build_modify_sltp_request(ticket: int, sl: float | None, tp: float | None) -> dict[str, Any]:
    """Build MT5 payload for modifying Stop Loss and Take Profit of a position."""
    trade_action_sltp = _mt5_const("TRADE_ACTION_SLTP", 6)
    return {
        "action": trade_action_sltp,
        "position": ticket,
        "sl": float(sl) if sl is not None else 0.0,
        "tp": float(tp) if tp is not None else 0.0,
    }


def build_pending_order_request(req: PendingOrderRequest, mt5_symbol: str, symbol_info: Any) -> dict[str, Any]:
    """Build MT5 payload for placing a pending order."""
    trade_action_pending = _mt5_const("TRADE_ACTION_PENDING", 5)
    order_time_gtc = _mt5_const("ORDER_TIME_GTC", 0)

    normalized_volume = normalize_lot_size(req.volume, symbol_info)
    from .order_mapper import pending_type_to_mt5_const
    order_type = pending_type_to_mt5_const(req.type)

    return {
        "action": trade_action_pending,
        "symbol": mt5_symbol,
        "volume": normalized_volume,
        "type": order_type,
        "price": float(req.price),
        "sl": float(req.sl) if req.sl else 0.0,
        "tp": float(req.tp) if req.tp else 0.0,
        "magic": 88001,
        "comment": _comment_normalizer.normalize(req.comment or "ai-hedge-fund pending order"),
        "type_time": order_time_gtc,
        "type_filling": resolve_filling_mode(symbol_info),  # T008–T009: dynamic resolution
    }


def build_modify_order_request(ticket: int, price: float | None, sl: float | None, tp: float | None) -> dict[str, Any]:
    """Build MT5 payload for modifying a pending order."""
    trade_action_modify = _mt5_const("TRADE_ACTION_MODIFY", 7)
    payload = {
        "action": trade_action_modify,
        "order": ticket,
        "sl": float(sl) if sl is not None else 0.0,
        "tp": float(tp) if tp is not None else 0.0,
    }
    if price is not None:
        payload["price"] = float(price)
    return payload


def build_cancel_order_request(ticket: int) -> dict[str, Any]:
    """Build MT5 payload for removing a pending order."""
    trade_action_remove = _mt5_const("TRADE_ACTION_REMOVE", 8)
    return {
        "action": trade_action_remove,
        "order": ticket,
    }
