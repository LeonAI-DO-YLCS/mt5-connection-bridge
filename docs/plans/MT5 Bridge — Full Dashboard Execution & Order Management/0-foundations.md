# Phase 0: Foundations — MetaTrader 5 Reference & Infrastructure

This phase establishes the technical groundwork for all subsequent phases. It includes the API capabilities reference, core safety architecture, and foundational model/mapper updates.

---

## 1. MT5 Python API Capabilities Reference

### Trade Actions

| Constant                | Value | Purpose                          |
| :---------------------- | :---- | :------------------------------- |
| `TRADE_ACTION_DEAL`     | 1     | Market order (instant execution) |
| `TRADE_ACTION_PENDING`  | 5     | Place pending order              |
| `TRADE_ACTION_SLTP`     | 6     | Modify SL/TP of open position    |
| `TRADE_ACTION_MODIFY`   | 7     | Modify pending order parameters  |
| `TRADE_ACTION_REMOVE`   | 8     | Delete pending order             |
| `TRADE_ACTION_CLOSE_BY` | 10    | Close by opposite position       |

### Order Types

| Constant                | Value | Purpose                                  |
| :---------------------- | :---- | :--------------------------------------- |
| `ORDER_TYPE_BUY`        | 0     | Market buy                               |
| `ORDER_TYPE_SELL`       | 1     | Market sell                              |
| `ORDER_TYPE_BUY_LIMIT`  | 2     | Buy at price ≤ specified (below market)  |
| `ORDER_TYPE_SELL_LIMIT` | 3     | Sell at price ≥ specified (above market) |
| `ORDER_TYPE_BUY_STOP`   | 4     | Buy at price ≥ specified (above market)  |
| `ORDER_TYPE_SELL_STOP`  | 5     | Sell at price ≤ specified (below market) |

### Key API Patterns

_Refer to [dashboard-full-execution-blueprint.md](../dashboard-full-execution-blueprint.md#3-mt5-python-api-capabilities-reference) for implementation snippets of Close, Pending, Modify, and Cancel patterns._

---

## 2. Infrastructure: Models & Mappers

### Base Changes required for all execution phases:

#### 2.1 Enhanced `TradeRequest` Model

```python
# app/models/trade.py
# Added SL/TP fields to support risk management in market orders
class TradeRequest(BaseModel):
    ticker: str
    action: Literal["buy", "sell", "short", "cover"]
    quantity: float
    current_price: float
    multi_trade_mode: bool = False
    sl: float | None = None          # Optional stop loss price
    tp: float | None = None          # Optional take profit price
```

#### 2.2 Updated `build_order_request` Mapper

```python
# app/mappers/trade_mapper.py
def build_order_request(trade_req, mt5_symbol, symbol_info):
    return {
        "action": TRADE_ACTION_DEAL,
        "symbol": mt5_symbol,
        "volume": normalized_volume,
        "type": order_type,
        "price": float(trade_req.current_price),
        "deviation": 20,
        "sl": float(trade_req.sl) if trade_req.sl else 0.0,
        "tp": float(trade_req.tp) if trade_req.tp else 0.0,
        "magic": 88001,
        "comment": "ai-hedge-fund mt5 bridge",
        "type_time": ORDER_TIME_GTC,
        "type_filling": ORDER_FILLING_IOC,
    }
```

#### 2.3 Position Mapper (Common Infrastructure)

```python
# app/mappers/position_mapper.py
def map_mt5_position_to_model(pos) -> Position:
    return Position(
        ticket=int(pos.ticket),
        symbol=str(pos.symbol),
        type="buy" if pos.type == 0 else "sell",
        volume=float(pos.volume),
        price_open=float(pos.price_open),
        price_current=float(pos.price_current),
        sl=float(pos.sl) if float(pos.sl) != 0.0 else None,
        tp=float(pos.tp) if float(pos.tp) != 0.0 else None,
        profit=float(pos.profit),
        swap=float(pos.swap),
        time=datetime.utcfromtimestamp(pos.time).isoformat() + "Z",
        magic=int(pos.magic),
        comment=str(pos.comment),
    )
```

---

## 3. Risk Assessment & Safety Architecture

All write operations inherit the existing safety layers:

| Layer                          | Mechanism                      | Applies To                          |
| :----------------------------- | :----------------------------- | :---------------------------------- |
| 1. `execution_enabled` gate    | ENV policy                     | All write endpoints                 |
| 2. API key auth                | `X-API-KEY` header             | All endpoints                       |
| 3. Single-flight / multi-trade | Concurrency control            | `/execute`, `/close-position`, etc. |
| 4. Slippage protection         | Pre-dispatch + post-fill check | Market execution & close            |
| 5. Pre-validation              | `mt5.order_check()`            | Pending orders (Phase 3)            |
| 6. Audit logging               | JSONL file log                 | All trade operations                |
| 7. UI confirmation             | Checkbox + modal               | Destructive actions in dashboard    |

---

## 4. Decision Matrix

### Architecture: Separate Endpoints vs Unified `/trade`

**Decision**: Separate Endpoints (Recommended)

- Each endpoint has one job (Account, Positions, Orders, Close, etc.).
- Self-documenting Swagger UI.
- Isolated test suites.
- Matches existing bridge architecture.

### UI: Card-Based vs Table-Based Positions

**Decision**: Position Cards (Recommended)

- Better fit for action buttons (Close, Modify SL/TP).
- Inline forms expand naturally.
- Mobile responsive (cards stack).
- Easier P&L color coding.
