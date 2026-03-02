# Data Model — MT5 Bridge Verification Dashboard

## Entity: DashboardSession

- **Purpose**: Represents authenticated dashboard access scope tied to browser tab session.
- **Fields**:
  - `api_key_present: bool`
  - `authenticated_at: datetime | null`
  - `terminated_reason: "tab_closed" | "browser_closed" | "credential_invalidated" | null`
- **Validation Rules**:
  - Session is authenticated only when API key validation succeeds.
- **State Transitions**:
  - `unauthenticated -> authenticated -> terminated`

## Entity: StatusSnapshot

- **Purpose**: Consolidated bridge and MT5 readiness view for Status tab.
- **Fields**:
  - `connected: bool`
  - `authorized: bool`
  - `broker: str | null`
  - `account_id: int | null`
  - `balance: float | null`
  - `latency_ms: int | null`
  - `worker_state: str`
  - `queue_depth: int`
- **Relationships**:
  - Combines `HealthStatus` + `WorkerStateSnapshot` + `MetricsSummary` slices.

## Entity: SymbolRecord

- **Purpose**: Exposes broker symbol mapping and trading metadata.
- **Fields**:
  - `ticker: str`
  - `mt5_symbol: str`
  - `lot_size: float`
  - `category: str`
- **Validation Rules**:
  - `ticker` unique within symbol map.
  - `lot_size > 0`.

## Entity: PriceQuery

- **Purpose**: Input payload abstraction for historical price retrieval.
- **Fields**:
  - `ticker: str`
  - `timeframe: "M1" | "M5" | "M15" | "M30" | "H1" | "H4" | "D1" | "W1" | "MN1"`
  - `start_date: date`
  - `end_date: date`
- **Validation Rules**:
  - `ticker` must exist in symbol map.
  - `start_date <= end_date`.
  - `timeframe` must be enum member.

## Entity: CandleRecord

- **Purpose**: Normalized OHLCV candle for UI table/chart and downstream compatibility.
- **Fields**:
  - `time: str` (ISO-8601 UTC)
  - `open: float`
  - `high: float`
  - `low: float`
  - `close: float`
  - `volume: int`
- **Validation Rules**:
  - `high >= max(open, close, low)`.
  - `low <= min(open, close, high)`.
  - `volume >= 0`.

## Entity: ExecutionVerificationRequest

- **Purpose**: Trade intent request captured from Execute tab.
- **Fields**:
  - `ticker: str`
  - `action: "buy" | "sell" | "short" | "cover"`
  - `quantity: float`
  - `current_price: float`
  - `multi_trade_mode: bool`
- **Validation Rules**:
  - `quantity > 0`.
  - `current_price > 0`.
  - Submission blocked when `execution_enabled = false`.
  - If `multi_trade_mode = false`, only one in-flight submission allowed.

## Entity: ExecutionResult

- **Purpose**: Outcome of one execution request.
- **Fields**:
  - `success: bool`
  - `filled_price: float | null`
  - `filled_quantity: float | null`
  - `ticket_id: int | null`
  - `error: str | null`
- **Validation Rules**:
  - If `success = true`, `ticket_id` and fill fields should be present.

## Entity: TradeAuditEntry

- **Purpose**: Durable execution trace line item.
- **Fields**:
  - `timestamp: str`
  - `request: object`
  - `response: object`
- **Relationships**:
  - Linked logically to one `ExecutionVerificationRequest` and one `ExecutionResult`.

## Entity: ConfigSnapshot

- **Purpose**: Sanitized runtime configuration for verification UI.
- **Fields**:
  - `mt5_bridge_port: int`
  - `mt5_server: str`
  - `mt5_login: int | null`
  - `mt5_path: str | null`
  - `log_level: str`
  - `symbol_count: int`
  - `symbols_config_path: str`
  - `execution_enabled: bool`
  - `metrics_retention_days: int`
- **Validation Rules**:
  - Must not include secrets (`mt5_bridge_api_key`, `mt5_password`).

## Entity: WorkerStateSnapshot

- **Purpose**: Detailed request-processing state for troubleshooting.
- **Fields**:
  - `state: str`
  - `queue_depth: int`
  - `max_reconnect_retries: int`
  - `reconnect_base_delay: float`
- **Validation Rules**:
  - `queue_depth >= 0`.

## Entity: MetricsSummary

- **Purpose**: Operational counters and retention visibility.
- **Fields**:
  - `uptime_seconds: float`
  - `total_requests: int`
  - `requests_by_endpoint: map[str, int]`
  - `errors_count: int`
  - `last_request_at: str | null`
  - `retention_days: int`
- **Validation Rules**:
  - `retention_days = 90`.
  - All counters non-negative.

## Relationship Overview

- `DashboardSession` reads `StatusSnapshot`, `SymbolRecord`, `ConfigSnapshot`, `WorkerStateSnapshot`, and `MetricsSummary`.
- `PriceQuery` returns `list[CandleRecord]` in `PriceResponse`.
- `ExecutionVerificationRequest` yields `ExecutionResult` and emits `TradeAuditEntry`.
