# Canonical Tracking ID Policy — MT5 Connection Bridge

> **Effective Date**: 2026-03-03
> **Format Version**: 1.0
> **Applies To**: All bridge responses (starting Phase 1 implementation)

---

## 1. Format Specification

### Pattern

```
brg-<YYYYMMDDTHHMMSS>-<hex4>
```

### Components

| Component         | Description                                             | Character Set            | Length |
| ----------------- | ------------------------------------------------------- | ------------------------ | ------ |
| `brg-`            | Fixed prefix identifying this as a bridge event         | Literal string           | 4      |
| `YYYYMMDDTHHMMSS` | UTC timestamp at generation time (compact ISO 8601)     | Digits `0-9`, letter `T` | 15     |
| `-`               | Separator                                               | Literal hyphen           | 1      |
| `<hex4>`          | Random hex suffix for uniqueness within the same second | Lowercase hex `0-9a-f`   | 4      |

### Constraints

- **Total length**: 24 characters (always fixed)
- **Character set**: lowercase `a-f`, digits `0-9`, hyphens `-`, uppercase `T`
- **URL-safe**: Yes — no encoding needed
- **Screenshot-safe**: Yes — readable in standard monospace fonts at typical dashboard zoom levels

### Worked Example

```
brg-20260303T094500-a3f7
│   │                │
│   │                └── Random hex: 0xa3f7 (42,999 of 65,536 possible values)
│   └── UTC timestamp: 2026-03-03 at 09:45:00
└── Bridge prefix
```

---

## 2. Generation Rules

1. **When**: A tracking ID is generated once per inbound HTTP request, at the earliest middleware entry point (before any route handler runs).

2. **How**: The ID is constructed by concatenating:
   - The literal prefix `brg-`
   - The current UTC time formatted as `%Y%m%dT%H%M%S`
   - A literal hyphen `-`
   - 4 random hexadecimal characters from `secrets.token_hex(2)`

3. **Uniqueness scope**: Per-runtime-session. The combination of timestamp + 4-hex-chars provides 65,536 unique IDs per second — sufficient for a single-operator bridge. IDs are not guaranteed unique across bridge restarts if the clock is identical to the second.

4. **Storage**: The generated ID is stored in the request scope (e.g., `request.state.tracking_id`) and is available to all downstream handlers, logging functions, and response formatters.

5. **Not generated for**: Static file requests (`/dashboard/*` static assets).

---

## 3. Propagation Path

The tracking ID flows through four stages:

```
┌─────────────┐     ┌──────────────────┐     ┌────────────────────┐     ┌──────────────────┐
│ 1. Generated │────►│ 2. Logged to JSONL│────►│ 3. Response Header │────►│ 4. Dashboard UI  │
│  (middleware) │     │  (audit module)   │     │  (X-Tracking-ID)   │     │  (message panel) │
└─────────────┘     └──────────────────┘     └────────────────────┘     └──────────────────┘
```

### Stage Details

| Stage                    | Component                                                                       | Field/Header                                           | Notes                                                                    |
| ------------------------ | ------------------------------------------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------ |
| **1. Generation**        | Request middleware in `app/main.py`                                             | `request.state.tracking_id`                            | Created before route dispatch                                            |
| **2. Structured log**    | `app/audit.py` → `logs/dashboard/trades.jsonl` and `logs/dashboard/tasks.jsonl` | `"tracking_id": "brg-..."`                             | Added as a top-level field in every JSONL log entry                      |
| **3. Response header**   | Response middleware or exception handler in `app/main.py`                       | `X-Tracking-ID: brg-...`                               | Attached to every HTTP response (success and error)                      |
| **4. Dashboard display** | `dashboard/js/app.js` or message panel component                                | Extracted from `response.headers.get('X-Tracking-ID')` | Shown in error/status messages so the operator can screenshot or copy it |

---

## 4. Log Correlation Guide

### Step-by-Step: From Dashboard Screenshot to Log Entry

**Given**: An operator sees a tracking ID in the dashboard (e.g., `brg-20260303T094500-a3f7`).

**Goal**: Find the full structured log entry within 60 seconds.

#### Step 1: Copy the tracking ID

From the dashboard error message, message panel, or response details — copy the full tracking ID string.

#### Step 2: Search the trade log

```bash
grep "brg-20260303T094500-a3f7" logs/dashboard/trades.jsonl
```

If no result, search the task/event log:

```bash
grep "brg-20260303T094500-a3f7" logs/dashboard/tasks.jsonl
```

#### Step 3: Read the matching entry

The output will be a single JSON line containing the full request, response, and metadata:

```json
{
  "timestamp": "2026-03-03T09:45:00.123456+00:00",
  "tracking_id": "brg-20260303T094500-a3f7",
  "request": { "action": "sell", "ticker": "EURUSD", "quantity": 0.1, ... },
  "response": { "success": false, "error": "order_send returned None: (-2, 'Invalid comment')" },
  "metadata": { "state": "order_send_none" }
}
```

#### Alternative: Search both logs at once

```bash
grep -r "brg-20260303T094500-a3f7" logs/dashboard/
```

#### Alternative: Search launcher session logs

If the event occurred during bridge startup or shutdown:

```bash
grep -r "brg-20260303T094500-a3f7" logs/bridge/launcher/
```

### Time-Based Estimation

The timestamp in the tracking ID (`20260303T094500`) gives you an approximate time. If the tracking ID is unclear in a screenshot, you can narrow the search:

```bash
grep "20260303T0945" logs/dashboard/trades.jsonl
```

This returns all entries from that minute, which should be a small set for a single-operator bridge.
