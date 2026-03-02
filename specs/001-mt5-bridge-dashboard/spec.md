# Feature Specification: MT5 Bridge Verification Dashboard

**Feature Branch**: `001-mt5-bridge-dashboard`  
**Created**: 2026-03-02  
**Status**: Draft  
**Input**: User description: "Read this file and create the artifact based on it: docs/plans/mt5-bridge-ui-blueprint.md"

## Clarifications

### Session 2026-03-02

- Q: How should execution access be controlled in the dashboard? → A: Keep one API key, but make execution disabled by default and only enabled explicitly per environment.
- Q: How should duplicate or rapid execution submissions be handled? → A: The system must allow multiple simultaneous trades with an operator toggle; when enabled, it must show risk guidance and still permit multiple submissions.
- Q: How long should operational metrics history be retained? → A: Retain metrics history for 90 days.
- Q: What concurrency limit should apply when multi-trade mode is enabled? → A: No explicit limit should be enforced.
- Q: What dashboard session lifetime should be enforced after inactivity? → A: No inactivity timeout; session remains active until browser or tab close.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verify Bridge Operations (Priority: P1)

As a bridge operator, I need a single verification dashboard that shows connection health and lets me retrieve market data so I can quickly confirm the bridge is usable before trading workflows run.

**Why this priority**: Operational verification is the gate for every downstream workflow; if this fails, trading and analysis cannot proceed safely.

**Independent Test**: Can be fully tested by authenticating to the dashboard, checking status indicators, fetching price data for a configured symbol, and confirming results or clear error messaging.

**Acceptance Scenarios**:

1. **Given** a valid API key and an operational bridge, **When** the operator opens the dashboard, **Then** current connection status, account context, and service health indicators are displayed.
2. **Given** a configured symbol and valid date range, **When** the operator requests historical prices, **Then** the system returns candle records with count and a readable no-data state when no records are available.

---

### User Story 2 - Safely Validate Trade Execution Flow (Priority: P2)

As a bridge operator, I need guarded execution verification so that I can test order submission behavior without accidental, unconfirmed real-trade requests.

**Why this priority**: Execution is high risk; safety confirmation and clear environment visibility are essential to prevent costly operator mistakes.

**Independent Test**: Can be fully tested by entering an execution request, observing mandatory safety confirmations, submitting, and reviewing success/failure output plus audit-log visibility.

**Acceptance Scenarios**:

1. **Given** an operator has filled trade details, **When** required confirmation steps are not completed, **Then** submission remains blocked.
2. **Given** all required confirmations are completed, **When** the operator submits an execution request, **Then** the system returns a clear result summary and records the outcome in the trade history view.

---

### User Story 3 - Regression-Safe Bridge Validation (Priority: P3)

As a QA engineer, I need a comprehensive automated verification suite for bridge behavior so regressions are detected early without needing a live broker terminal.

**Why this priority**: Stable delivery requires repeatable quality checks; manual-only validation is slow and misses edge-case regressions.

**Independent Test**: Can be fully tested by running the verification suite in a non-production environment and confirming pass/fail outcomes across core bridge behaviors.

**Acceptance Scenarios**:

1. **Given** the verification suite is executed in CI or local test mode, **When** core bridge behaviors are unchanged, **Then** all required tests pass without requiring live terminal connectivity.
2. **Given** a regression is introduced in mapping, authentication, worker state handling, or endpoint behavior, **When** the verification suite runs, **Then** at least one targeted test fails with a diagnosable error.

---

### Edge Cases

- How the system responds when API credentials are missing, invalid, or expired during dashboard use.
- How price requests behave when a symbol exists but no candles are available for the selected period.
- How all dashboard tabs degrade when the bridge is disconnected or temporarily unavailable.
- How trade-history views behave when no audit file exists or the log is empty.
- How pagination and filtering behave with high-volume audit history.
- How safety controls behave when account context cannot be resolved.
- How concurrent execution requests behave when multi-trade mode is disabled versus enabled.
- How metrics visibility behaves when data exceeds the retention window.
- How very high concurrent submission bursts are communicated to operators when no explicit concurrency cap is enforced.
- How authentication state behaves across long-running sessions without inactivity timeout.
- How execution behavior is surfaced when slippage tolerance is exceeded or fill confirmation is delayed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST require API-key authentication before showing verification dashboard data.
- **FR-002**: The system MUST provide a consolidated status view that includes connection health, authorization state, account context, latency, worker state, and request activity.
- **FR-003**: The system MUST provide a symbol catalog view that supports search and category-based filtering.
- **FR-004**: The system MUST allow operators to request historical prices using ticker, date range, and timeframe inputs.
- **FR-005**: The system MUST present returned price records in both tabular form and visual trend form, and allow export of fetched results.
- **FR-006**: The system MUST present user-readable error states for unauthorized access, disconnected service, invalid inputs, and empty data responses, and each error state MUST include both the failure reason and the next operator action.
- **FR-007**: The system MUST provide an execution verification flow with explicit environment visibility (live or demo), required acknowledgment, and final confirmation before submission.
- **FR-008**: The system MUST display execution outcomes with explicit details including attempted action, ticker, quantity, success flag, and either fill details or failure reason.
- **FR-009**: The system MUST provide paginated trade-history visibility with refresh capability.
- **FR-010**: The system MUST provide a read-only runtime configuration view that excludes secrets and sensitive credentials, and includes non-secret execution policy fields (`execution_enabled`, `metrics_retention_days`, and `multi_trade_overload_queue_threshold`).
- **FR-011**: The system MUST provide granular worker-state visibility to support troubleshooting.
- **FR-012**: The system MUST preserve backward compatibility for existing bridge consumers that rely on current data and execution contracts.
- **FR-013**: The system MUST include automated tests that cover authentication, data mapping, worker behavior, current endpoints, and newly added verification capabilities.
- **FR-014**: The automated tests MUST run without requiring live broker connectivity by using controlled simulation of terminal interactions.
- **FR-015**: The system MUST keep execution actions disabled by default and require an explicit environment-level enablement before any execution request can be submitted.
- **FR-016**: The system MUST provide an operator-controlled toggle to enable or disable multiple simultaneous trade submissions.
- **FR-017**: When multi-trade mode is enabled, the system MUST display an explicit risk-management warning before allowing simultaneous trade submissions.
- **FR-018**: When multi-trade mode is enabled, the system MUST allow submission of multiple trades in parallel without enforcing a single-trade lock.
- **FR-019**: When multi-trade mode is disabled, the system MUST prevent overlapping execution submissions and present a clear message explaining that only one active submission is allowed at a time.
- **FR-020**: The system MUST retain operational metrics history for 90 days to support troubleshooting and trend review.
- **FR-021**: When multi-trade mode is enabled, the system MUST not enforce a fixed numeric concurrency cap and MUST continue accepting concurrent submissions until overload protection is triggered; overload protection MUST trigger when worker queue depth reaches `multi_trade_overload_queue_threshold` (default: 100 pending submissions), after which the system MUST reject new submissions with explicit overload reason and retry guidance.
- **FR-022**: The dashboard session MUST remain active without an inactivity timeout and only end when the browser or tab session is closed, or when credentials are invalidated.
- **FR-023**: The system MUST preserve existing MT5 adapter support for real-time tick/bar streaming capability without regression while delivering this feature.
- **FR-024**: The execution verification flow MUST enforce pre-dispatch slippage protection by rejecting execution attempts whose projected fill exceeds configured slippage tolerance.
- **FR-025**: The system MUST update execution state and persisted execution outcome only after definitive fill or rejection confirmation is received from the MT5 adapter; if confirmed fill exceeds configured slippage tolerance, the outcome MUST be recorded as a slippage-violation exception with explicit operator-facing remediation guidance.

### Assumptions

- The dashboard verifies a single bridge instance at a time.
- Operators already have authorized API keys through existing access controls.
- Trade logs may be empty and should still render as a valid state.
- New dashboard live-streaming UI controls are out of scope for this feature, but existing MT5 adapter tick/bar streaming capability remains in scope for non-regression.

### Dependencies

- Existing bridge health, price retrieval, and execution capabilities remain available.
- Configured symbols remain the source for selectable instruments.
- Audit logging remains enabled for execution history visibility.

### Key Entities *(include if feature involves data)*

- **Dashboard Session**: An authenticated operator session used to access verification capabilities.
- **Status Snapshot**: Current operational state values used to determine bridge readiness.
- **Symbol Record**: A configured tradable instrument entry with display and sizing metadata.
- **Price Query**: A user-defined request for historical market data bounded by instrument, timeframe, and date range.
- **Candle Record**: A single OHLCV data point returned from a price query.
- **Execution Verification Request**: Operator-submitted trade intent used to validate execution flow.
- **Execution Result**: Outcome payload containing success/failure details, identifiers, fill confirmation state, and slippage-protection rejection reason when applicable.
- **Trade Audit Entry**: Historical record of execution requests and responses for traceability.
- **Config Snapshot**: Sanitized runtime settings used for operational validation.
- **Worker State Snapshot**: Queue and lifecycle indicators representing bridge request-processing health.
- **Verification Suite**: Automated quality checks validating required bridge behaviors.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 95% of operators can confirm bridge readiness (status + price fetch) within 2 minutes during acceptance testing, measured across a minimum sample of 20 operator-run readiness checks using the documented quickstart validation protocol.
- **SC-002**: 100% of execution submissions initiated from the dashboard require completion of all mandatory confirmation controls before request dispatch.
- **SC-003**: At least 99% of dashboard data interactions (status, symbols, prices, logs, config) return results or actionable error messaging within 3 seconds under normal operating load (defined as 20 concurrent operator sessions and a seeded 1,000-entry log dataset).
- **SC-004**: Automated verification coverage includes all critical bridge behaviors and reaches at least 90% statement coverage on bridge modules.
- **SC-005**: For a seeded audit history of 1,000 entries, operators can load and navigate log pages with median page-load time under 2 seconds.
- **SC-006**: Existing bridge client workflows for health checks, price retrieval, and trade submission show zero contract-breaking changes in regression validation.
- **SC-007**: Operators can retrieve and review at least 90 consecutive days of retained operational metrics during validation.
- **SC-008**: MT5 adapter real-time tick/bar streaming capability remains functionally unchanged in regression validation after this feature is delivered.
- **SC-009**: 100% of accepted execution outcomes in validation runs are recorded only after definitive MT5 fill or rejection confirmation, and all slippage-tolerance violations are rejected or exception-classified with explicit operator-facing reason messaging, validated through a consolidated execution-safety acceptance report.
