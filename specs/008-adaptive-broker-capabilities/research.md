# Research: Adaptive Broker Capabilities

**Feature**: 008-adaptive-broker-capabilities
**Date**: 2026-03-02
**Status**: Complete — all decisions resolved

---

## D-001: Filling Mode Resolution Strategy

**Decision**: Resolve filling mode dynamically per symbol using a priority cascade: FOK → IOC → RETURN.

**Rationale**:

- MT5 exposes `symbol_info.filling_mode` as an integer bitmask where bit 0 = FOK supported, bit 1 = IOC supported. When the bitmask is 0, only RETURN applies (it is MT5's implicit always-supported fallback).
- FOK (Fill or Kill) is preferred for market orders because it is atomic — either the entire volume fills or nothing does, preventing partial fills that would complicate position tracking.
- RETURN is always safe because MT5 guarantees it is supported for all symbols; it fills what is available and returns the remainder as a pending order fragment.
- Hardcoding IOC (as the current code does) fails on brokers like Deriv that use RETURN-only for some instrument classes (e.g., synthetic indices).

**Alternatives considered**:

- Always use RETURN: Safe but suboptimal on brokers that support FOK — FOK gives cleaner execution semantics.
- Expose filling mode as a user-configurable per-symbol setting in `symbols.yaml`: Rejected — adds operational burden and defeats the purpose of dynamic capability detection.
- Cache the resolved filling mode per symbol: Adopted as part of the `/broker-capabilities` cache (filling mode rarely changes).

**Implementation**: New `resolve_filling_mode(symbol_info) -> int` function in `app/mappers/trade_mapper.py`. Applied to `build_order_request()`, `build_pending_order_request()`, and `build_close_request()`.

---

## D-002: Broker Capabilities Endpoint — Cache Strategy

**Decision**: In-memory module-level dict with a configurable TTL (default 60 seconds), invalidated on MT5 worker reconnect.

**Rationale**:

- The capabilities catalog (symbol list, trade modes, filling modes, paths) changes very rarely — only when a broker adds/removes instruments or changes account permissions. 60 seconds is safely fresh for dashboard use.
- In-memory storage is appropriate because: (1) the MT5 bridge is a single-process Windows service, (2) there is no horizontal scaling, (3) persistence across restarts is unnecessary since MT5 must be reconnected anyway.
- A module-level `_capabilities_cache` dict with `_cache_fetched_at: datetime` allows both TTL checks and forced invalidation without external dependencies.
- The MT5 worker reconnect event is the correct invalidation trigger because a brokers symbol list may change between sessions (e.g., temporary suspensions).

**Alternatives considered**:

- Redis cache: Overkill for a single-process service. Adds an unnecessary external dependency.
- File-based cache (JSON): Adds I/O complexity, potential corruption, and offers no real benefit over in-memory for a service that must reconnect anyway.
- No caching (call MT5 on every request): `symbols_get()` can return 1000+ records and is a synchronous MT5 IPC call; calling it on every dashboard poll would cause measurable latency.

**TTL Configuration**: `CAPABILITIES_CACHE_TTL_SECONDS` env var, default `60`. Validated in `app/config.py`.

---

## D-003: Symbol Path Parsing for Category Extraction

**Decision**: Split on both `\` and `/` (normalize to `/` first), take segment 0 as category and segment 1 as subcategory.

**Rationale**:

- MT5 on Windows uses `\` as the path separator, but some brokers may use `/` (Deriv has been observed using both in different contexts).
- Normalizing first with `path.replace("\\", "/")` then splitting on `/` handles both cases uniformly.
- Segment 0 (e.g., `"Forex"`) is the top-level category folder in MT5's Symbols tree — exactly what the dashboard category filter should show.
- Segment 1 (e.g., `"Majors"`) is the subcategory for finer grouping.
- Empty path fallback: assign category `"Other"`, subcategory `""`.

**Alternatives considered**:

- Using `symbol_info.category_type` (MT5 constant int): Present in some MT5 versions but not consistently populated across brokers. Path parsing is more reliable and portable.
- Using the `group` parameter of `mt5.symbols_get(group=...)` to enumerate categories: Would require multiple API calls. Path parsing achieves the same result in a single `symbols_get()` call.

---

## D-004: Dashboard Ticker Dropdown — Usability with Large Catalogs

**Decision**: Use `<optgroup>` tags for category grouping plus a text search/filter `<input>` above the dropdown, with client-side filtering on the already-loaded capabilities data.

**Rationale**:

- Some brokers (e.g., Deriv) offer 1000+ symbols. A flat `<select>` of 1000 options is unusable.
- `<optgroup>` provides native browser grouping with zero JS complexity, matching the MT5 category hierarchy exactly.
- Adding a text search input above the select box allows typing to filter the visible `<option>` elements (via JS `display: none` toggling on non-matching options) — no server round-trip needed since all data is already loaded from `/broker-capabilities`.
- The capabilities payload is fetched once per tab open and held in memory, so search filtering is instant.

**Alternatives considered**:

- Server-side search with `GET /broker-symbols?name=EUR*`: Adds a round-trip per keystroke. Unnecessary since the full catalog is already loaded.
- Virtual scroll list (custom component): Excessive complexity for a developer-facing dashboard.
- Paginated dropdown with API calls: Same server-round-trip problem.

---

## D-005: Trade Mode Enforcement — Where to Validate

**Decision**: Inside the MT5 worker closure (inside `_execute_in_worker()`) immediately after `symbol_info` is fetched, before building the order request.

**Rationale**:

- `symbol_info` is already fetched at this point for other reasons (volume normalization, fill mode). Reusing it for trade mode validation adds zero extra MT5 IPC calls.
- Validating inside the worker ensures the freshest trade mode data (not stale cache) is used, which matters because brokers can temporarily change a symbol's trade mode (e.g., weekend close-only mode).
- The validation must happen inside `submit()` because `symbol_info` is only available in the MT5 worker thread.

**Alternatives considered**:

- Pre-validate using cached capabilities data before dispatching to worker: Faster but risks acting on stale data (e.g., symbol moved to close-only between cache update and order dispatch). The worker-side check is the authoritative gate.
- Add a dedicated pre-flight check endpoint: Rejected — over-engineering for a validation that is a single `if` block.

---

## D-006: Backward Compatibility for `/execute` with YAML Tickers

**Decision**: Keep `symbol_map` (YAML-based) as the ticker resolution source for `POST /execute` and `POST /pending-order`. The dashboard's Execute tab will send the MT5 symbol name directly (from the broker catalog) rather than a YAML alias.

**Rationale**:

- The YAML `symbol_map` serves the AI hedge fund agents that use tickers like `V75`, `EURUSD`. These are stable aliases that strategies are coded against. Breaking them is unacceptable.
- The dashboard is not an AI strategy — it is an operator tool. It can work directly with MT5 symbol names once it fetches them from `/broker-capabilities`.
- For dashboard-originated executions using symbols not in YAML, the `POST /execute` endpoint needs to be extended to optionally accept a raw MT5 symbol name directly (bypassing the YAML lookup).

**Decision addendum**: Add optional field `mt5_symbol_direct: str | None` to `TradeRequest`. If present, it short-circuits the YAML symbol_map lookup. This is only used by the dashboard for symbols not configured in YAML.

**Alternatives considered**:

- Require all new symbols to be added to `symbols.yaml` first: Defeats the entire purpose of dynamic discovery.
- Replace YAML lookup entirely with broker catalog: Would break all existing AI strategy API calls.
- Use a separate `/execute-direct` endpoint for raw MT5 symbols: Adds surface area without benefit. Optional field is cleaner.

---

## D-007: update-agent-context.sh Script Result

Running `.specify/scripts/bash/update-agent-context.sh agy` adds the bridge's technical context to the agent file. No new technology is introduced by this feature — all additions use existing Python/FastAPI/Pydantic/Vanilla JS patterns already present in the project.

---

## Summary of Research Outcomes

| Decision             | Outcome                                                                   |
| -------------------- | ------------------------------------------------------------------------- |
| Filling mode         | Priority cascade: FOK → IOC → RETURN, resolved per-symbol via bitmask     |
| Cache strategy       | In-memory TTL (60s default), invalidated on worker reconnect              |
| Path parsing         | Normalize separator → split → segment[0]=category, segment[1]=subcategory |
| Dropdown UX          | `<optgroup>` + text search input, client-side filter                      |
| Validation placement | Inside MT5 worker closure, after `symbol_info` fetch                      |
| Backward compat      | Keep YAML aliases; add optional `mt5_symbol_direct` to `/execute`         |
