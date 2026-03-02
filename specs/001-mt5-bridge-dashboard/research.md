# Research — MT5 Bridge Verification Dashboard

## 1. Dashboard Authentication for FastAPI Static UI

**Decision**: Use same-origin static UI served by FastAPI with `X-API-KEY` header supplied from `sessionStorage` per request.

**Rationale**: Same-origin static serving avoids CORS complexity, keeps auth model consistent with existing bridge routes, and ensures session ends on tab/browser close.

**Alternatives considered**:
- Cookie/session auth: rejected because it introduces backend session state and diverges from existing API-key model.
- LocalStorage token: rejected because persistence beyond tab lifetime conflicts with chosen session safety posture.

## 2. Real-Account Execution Gating

**Decision**: Execution is disabled by default via environment policy; dashboard execute actions are blocked unless `execution_enabled=true` is exposed via `/config`.

**Rationale**: Default-off gating is the strongest preventive control for live money operations and satisfies explicit execution safety constraints.

**Alternatives considered**:
- Always-enabled execution with only confirmations: rejected due to higher accidental execution risk.
- Separate API keys for execution and read-only: deferred to future hardening; not required for current additive scope.

## 3. Concurrent Submission Handling

**Decision**: Provide a user-facing multi-trade toggle; OFF enforces single in-flight submission, ON allows parallel submissions with no fixed cap and mandatory risk warning.

**Rationale**: This matches clarified product behavior while preserving operator awareness of risk and allowing power-user workflows.

**Alternatives considered**:
- Global hard cap (5/10/20): rejected by clarified requirement (`no fixed cap when enabled`).
- Always single-flight only: rejected because it blocks intended multi-order workflows.

## 4. Metrics Retention

**Decision**: Persist metrics summaries with rolling 90-day retention using `logs/metrics.jsonl` and prune older records.

**Rationale**: Meets explicit requirement for 90-day visibility while bounding storage and making retention behavior deterministic.

**Alternatives considered**:
- In-memory only metrics: rejected because it cannot satisfy 90-day retention.
- 30 or 365 day window: rejected due to explicit clarified requirement of 90 days.

## 5. MT5 Testability in Linux/CI

**Decision**: Fully mock the `MetaTrader5` module and MT5-dependent behaviors in pytest fixtures to make tests OS-independent.

**Rationale**: MT5 package is Windows-only; full mocking allows deterministic unit/integration testing in Linux CI pipelines.

**Alternatives considered**:
- Windows-only integration test pipeline: deferred; useful later but insufficient as primary CI strategy.
- Partial mocking with live terminal dependency: rejected due to flaky and environment-coupled tests.

## 6. Contract Documentation Strategy

**Decision**: Use a single `contracts/openapi.yaml` as the contract source for existing and additive endpoints.

**Rationale**: OpenAPI provides endpoint + schema coverage, clear compatibility tracking, and simpler client/QA alignment than separate ad hoc files.

**Alternatives considered**:
- JSON schema files only: rejected because endpoint-level operations and status mappings are incomplete.
- OpenAPI + separate JSON schemas: rejected due to drift risk and unnecessary duplication for this scope.

## Clarification Lock-In Mapping

- Execution default-off: enforced by Decision 2.
- Multi-trade toggle behavior: enforced by Decision 3.
- No fixed cap in multi-trade mode: enforced by Decision 3.
- Metrics retention at 90 days: enforced by Decision 4.
- No inactivity timeout while tab open: enforced by Decision 1.
