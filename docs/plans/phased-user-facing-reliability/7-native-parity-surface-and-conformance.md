# Phase 7: Native Parity Surface and Conformance

> Objective: Move toward broad MT5 Python-library parity in a controlled way, without sacrificing safety for standard operators.

---

## 1. Parity Strategy

Parity cannot mean “single behavior across all brokers.”  
Parity must mean:

1. broad API coverage
2. capability-aware behavior
3. deterministic fallback policies
4. explicit conformance reporting

---

## 2. Dual API Surface Model

### 2.1 Safe domain API (default)

Purpose:

- operations by intent (execute, close, modify, cancel)
- strict readiness and policy guardrails
- human-readable message contract

### 2.2 Advanced raw MT5 namespace

Purpose:

- expert-level control with near 1:1 MT5 function exposure
- explicit “advanced mode” semantics and safety disclaimers

Potential namespace:

- `/mt5/raw/*`

---

## 3. Coverage Matrix Plan

Map MT5 Python library categories to bridge surfaces:

1. connection/session lifecycle
2. terminal/account metadata
3. symbol and market data
4. order pre-check and calculations
5. order submission and management
6. history and reporting
7. optional advanced facilities (market book, etc.)

Initial capability mapping baseline:

1. Already represented:
   - account/terminal info
   - symbols and tick data
   - historical rates
   - order send/check and management flows
2. Commonly missing or partial for parity:
   - explicit margin/profit calculation surfaces
   - deeper order-book/market-book features
   - richer terminal/session introspection for expert tooling
   - complete retcode/last-error translation coverage.

For each mapped capability track:

- implemented status
- constraints
- known broker variance
- fallback behavior
- test coverage
- operator-facing readiness impact.

---

## 4. Decision Matrix: Parity Rollout

| Option | Description | Pros | Cons | Recommendation |
|---|---|---|---|---|
| A | Implement raw parity first | Broad quickly | High safety/support risk | No |
| B | Safe API only forever | Stable | Caps advanced utility | No |
| C | Safe-first baseline, then gated advanced namespace + conformance harness | Balanced and scalable | Longer roadmap | **Recommended** |

---

## 5. Conformance Harness

Introduce a broker/terminal conformance suite that validates:

1. endpoint behavior across key operation classes.
2. readiness checks vs runtime outcomes.
3. retcode/error normalization consistency.
4. fallback behavior correctness (including comment compatibility).
5. launcher/runtime diagnostics integrity.

Conformance report dimensions:

1. broker + server name
2. terminal build/version
3. python runtime context
4. compatibility profile used
5. pass/fail/warn by capability area
6. recommended runtime mode for production.

Outputs:

- conformance report per broker/environment
- gap list and recommended compatibility mode.

---

## 6. Operational Compatibility Modes

Define runtime compatibility profiles:

- `strict_safe`
- `balanced`
- `max_compat`

Each profile defines:

1. retry/fallback aggressiveness
2. optional field handling policy
3. gating strictness
4. user-facing warning verbosity.

Profiles must be explicit, auditable, and reversible.

---

## 7. Governance Requirements

1. Any new raw endpoint must define:
   - safety classification
   - authentication behavior
   - redaction/logging policy
   - readiness interaction policy.
2. Safe API remains the default recommendation in dashboard and docs.
3. Advanced namespace remains clearly labeled as expert-only.

---

## 8. Exit Criteria

1. Coverage matrix exists and is continuously maintained.
2. Conformance harness can be run before production rollout.
3. Advanced parity endpoints are documented with strong guardrails.
4. Operators can select compatibility mode knowingly.
