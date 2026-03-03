# Phase 4: History & Discovery — Analytics & Market Exploration

**Goal**: Provide a full trade audit trail from MT5 (deals and closed orders), broker symbol discovery, and CSV export capabilities.

---

## 1. Backend Endpoints (History & Discovery)

### 1.1 `GET /history/deals` — Deal History (Fills)

- **Purpose**: Retrieve historical MT5 deals (including manual trades & external EAs).
- **Parameters**: `date_from`, `date_to`, `symbol` (optional), `position` (optional).
- **Model**: `ticket`, `order_ticket`, `position_id`, `symbol`, `type`, `entry` (in/out), `volume`, `price`, `profit`, `swap`, `commission`, `fee`, `time`, `magic`.

### 1.2 `GET /history/orders` — Historical Order Records

- **Purpose**: Retrieve historical (completed/cancelled) orders.
- **Model**: Includes `state` (filled, cancelled, expired, rejected).

### 1.3 `GET /broker-symbols` — Discover All Broker Symbols

- **Purpose**: List ALL symbols available from the broker, not just those in `symbols.yaml`.
- **Query**: `group` (e.g., "_USD_", "Forex\*").
- **Model**: `name`, `description`, `path`, `spread`, `digits`, `volume_min/max`, `trade_mode`, `is_configured`.

---

## 2. Dashboard: New Analytics Tabs

### 2.1 Trade History Tab

- **Sub-tabs**: Deals (Fills) vs Orders (Records).
- **Date Range Picker**: Filter history by start/end date.
- **Export**: _"Export to CSV"_ button for the current table view.
- **Summary Header**: Display Net Profit, Total Swap, Total Commission, and Trade Count for the selected period.

### 2.2 Broker Symbols Browser (Integrated into Symbols Tab)

- Search entire broker catalog.
- Group filtering (Forex, Indices, Crypto, etc.).
- "Is Configured" status badge.
- Quick link to add a discovered symbol to the local bridge configuration.

---

## 3. Implementation Notes

### History Date Conversion

MT5 uses standard UNIX timestamps for historical queries. The bridge endpoints will accept ISO 8601 strings and convert them internally to timestamps for appropriate `mt5.history_deals_get` / `mt5.history_orders_get` calls.

---

## 4. Deliverable

A complete trade history audit trail, the ability for users to discover and browse any symbol offered by their broker, and the capacity to export trade data to CSV for external analysis.
