from datetime import datetime, timezone

from ..models.position import Position


def map_mt5_position(pos) -> Position:
    """
    Map an MT5 position namedtuple to the Position Pydantic model.
    """
    return Position(
        ticket=pos.ticket,
        symbol=pos.symbol,
        type="buy" if pos.type == 0 else "sell",
        volume=float(pos.volume),
        price_open=float(pos.price_open),
        price_current=float(pos.price_current),
        sl=float(pos.sl) if pos.sl > 0.0 else None,
        tp=float(pos.tp) if pos.tp > 0.0 else None,
        profit=float(pos.profit),
        swap=float(pos.swap),
        time=datetime.fromtimestamp(pos.time, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + "Z",
        magic=pos.magic,
        comment=pos.comment,
    )
