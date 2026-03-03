# Terminology Glossary — MT5 Connection Bridge

> **Snapshot Date**: 2026-03-03
> **Last Reviewed**: 2026-03-03
> **Applies To**: All phased user-facing reliability work (Phases 0–7)

---

## Core Terms

| Term         | Definition                                                                                                                                                                                                                                                             | Example Trigger                                                                                                                                            | Dashboard Treatment                                                                                                                                                                            |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **error**    | An operation was attempted and failed — it cannot complete as requested. The operator may be able to retry or adjust parameters, but the current request has produced a definitive failure.                                                                            | `order_send returned None: (-2, 'Invalid "comment" argument')` in `close_position.py`. An MT5 order was submitted but rejected by the broker or terminal.  | **Red banner** with error message text, error code, and tracking ID. Persists until dismissed or replaced by a new operation result.                                                           |
| **warning**  | A condition exists that may cause problems or restrict available actions, but does not prevent the current operation from proceeding. The operator should be aware but no immediate action is strictly required.                                                       | Symbol `trade_mode=1` (Long Only) — the operator can still view the symbol and place buy orders, but sell orders will be rejected if attempted.            | **Orange inline alert** near the relevant control (e.g., next to the Sell button). Shown when the condition is detected, removed when the condition changes.                                   |
| **status**   | A neutral factual event or state change requiring no operator action. Used to confirm that something happened or to report the current state of the system.                                                                                                            | Worker state transition from `CONNECTING` to `AUTHORIZED` — the MT5 terminal connected and logged in successfully.                                         | **Info text** (muted/gray) in the status panel or log timeline. No visual emphasis — these are background confirmations.                                                                       |
| **advice**   | A recommended action for the operator to improve outcomes or prevent future problems. Not blocking, not urgent, but worth considering. The system has observed a condition that experience suggests should be addressed proactively.                                   | "Consider restarting bridge — uptime exceeds 72 hours" — the bridge has been running for an extended period and may benefit from a fresh connection cycle. | **Blue suggestion box** with a recommended action label. Shown in the status panel or as a non-intrusive notification. Can be dismissed.                                                       |
| **blocker**  | A system-level condition that prevents **all** operations until resolved. The bridge or terminal is in a state where no trade, query, or data operation can succeed. The operator must take external action (restart, reconfigure, contact broker) to restore service. | Worker state `DISCONNECTED` after exhausting all 5 reconnection attempts — the MT5 terminal is unreachable and cannot process any requests.                | **Red lock overlay** covering the main content area with a clear message explaining what is blocked and what the operator should do. No controls are actionable until the blocker is resolved. |
| **recovery** | A previously failed or blocked condition has resolved itself, either through automatic retry or external intervention. This confirms that the system has returned to a healthy state.                                                                                  | Successful reconnect after `RECONNECTING` state — the worker re-established the MT5 connection after a temporary disconnection.                            | **Green transient toast** (auto-dismiss after 5–10 seconds) confirming the recovery. Optionally logged in the operator timeline.                                                               |

---

## Severity Scale

| Level        | Criteria                                                                                                                                                                                                                              | Action Required                                                                                                                                                  | Example                                                                                                                                                                                   |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **critical** | System unavailable or operation unsafe. The bridge cannot serve any requests, or continuing to operate would risk unintended trades or data loss.                                                                                     | **Immediate attention**. Stop all trading activity. Investigate and resolve before resuming. Escalate to system administrator if needed.                         | MT5 terminal disconnected after all 5 reconnection retries — worker state is `DISCONNECTED`. No MT5 operations can execute.                                                               |
| **high**     | A specific operation category is blocked, or a policy prevents execution. The bridge is running but cannot perform the requested action. Operator intervention is needed to change configuration or resolve the underlying condition. | **Operator action needed**. Review the specific block condition and either change configuration, update parameters, or wait for the external condition to clear. | `EXECUTION_DISABLED` policy is active (`EXECUTION_ENABLED=false`) — all trade submissions are rejected with HTTP 403. The operator must update the environment variable or runtime state. |
| **medium**   | An operation was blocked, but the issue is user-correctable. The operator can resolve the problem by adjusting their input (changing parameters, selecting a different symbol, etc.) without system-level intervention.               | **Adjust and retry**. Read the error message, correct the input, and resubmit. No system configuration change needed.                                            | Close position requested with invalid volume step size — volume `0.03` does not align with the symbol's `volume_step=0.02`. The operator should adjust to `0.02` or `0.04`.               |
| **low**      | Non-blocking advisory or informational notice. The system is healthy and operational. This notice provides context or a proactive suggestion that the operator may choose to act on — or safely ignore.                               | **No action required** to continue operating. Consider the advice at your convenience.                                                                           | Stale tick data — the last tick for a symbol is older than 5 minutes. The data is still available but may not reflect current market conditions.                                          |

---

## Usage Notes

### How to Categorize a New Runtime Event

When a new event type is introduced in any phase, follow this process:

1. **Identify the scope**: Does this event affect one operation, one feature category, or the entire system?
   - Single operation → likely `error` or `warning`
   - All operations → likely `blocker` or `status`
   - No operations (advisory) → likely `advice`
   - Resolution of prior failure → `recovery`

2. **Match the term**: Read the definitions above and select the single best match. If the event has characteristics of two terms, prefer the more specific one (e.g., prefer `blocker` over `error` if the condition prevents all operations).

3. **Assign severity**: Use the criteria column in the severity scale. The key question is: "What must the operator do right now?"
   - Nothing → `low`
   - Fix their input → `medium`
   - Change system state → `high`
   - Stop everything → `critical`

4. **Note the dashboard treatment**: Every new event type must specify how it renders on the dashboard, consistent with the treatment column in the core terms table. Phase 6 (Dashboard Operator Experience) will implement these treatments.

### Cross-Reference with Error Codes

Every `error`-term event should have a corresponding entry in the [error-code namespace](./error-code-namespace.md). The error code provides the machine-readable identity; the glossary term provides the human-readable category.
