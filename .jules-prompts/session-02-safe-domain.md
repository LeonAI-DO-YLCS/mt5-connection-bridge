## Context — Phase 7: Native Parity Surface and Conformance

You are implementing **Phase 7 — Native Parity Surface and Conformance** for the **MT5 Connection Bridge** project.
Branch: `016-phase7-native-parity-surface-and-conformance`

### Required Reading (READ BEFORE WRITING CODE)

Read these files in the repository for full context:

- `specs/016-phase7-native-parity-surface-and-conformance/tasks.md` — your task list (execute ONLY the tasks listed below)
- `specs/016-phase7-native-parity-surface-and-conformance/plan.md` — architecture, tech stack, project structure
- `specs/016-phase7-native-parity-surface-and-conformance/data-model.md` — entity schemas (MarginCheckRequest/Response, ProfitCalcRequest/Response)
- `specs/016-phase7-native-parity-surface-and-conformance/contracts/api-contracts.md` — API contracts for POST /margin-check and POST /profit-calc
- `app/routes/__init__.py` — existing router registration pattern
- `app/routes/order_check.py` — existing order-check route pattern (follow same canonical envelope wrapping)
- `app/mt5_worker.py` — worker `submit()` function for MT5 calls
- `app/config.py` — `get_settings()` and symbol resolution helpers
- `app/auth.py` — `api_key_dependency` for route authentication

### Your Tasks — Phase 2: US1 — Safe Domain Extensions (MVP)

Execute ONLY these tasks from `specs/016-phase7-native-parity-surface-and-conformance/tasks.md`:

- [ ] T007 [P] [US1] Create `MarginCheckRequest` and `MarginCheckResponse` Pydantic models in `app/models/margin.py` per data-model.md
- [ ] T008 [P] [US1] Create `ProfitCalcRequest` and `ProfitCalcResponse` Pydantic models in `app/models/margin.py` (same file, co-located)
- [ ] T009 [US1] Implement `POST /margin-check` route in `app/routes/margin_check.py`: validate request, resolve symbol via `symbol_map`, call `mt5.order_calc_margin()` through worker `submit()`, wrap in canonical envelope, gate on readiness (worker state must be `AUTHORIZED`)
- [ ] T010 [US1] Implement `POST /profit-calc` route in `app/routes/profit_calc.py`: validate request, call `mt5.order_calc_profit()` through worker `submit()`, wrap in canonical envelope, readiness-gated
- [ ] T011 [US1] Register `margin_check_router` and `profit_calc_router` in `app/routes/__init__.py` and mount in the FastAPI app
- [ ] T012 [US1] Write unit tests for margin-check and profit-calc in `tests/unit/test_margin_check.py` and `tests/unit/test_profit_calc.py` — mock `mt5.order_calc_margin` and `mt5.order_calc_profit`, verify canonical envelope shape, error codes, readiness gating

### Rules

1. **Read first**: Read every file you are about to modify BEFORE making changes.
2. **Follow exactly**: Each task specifies the exact file, function, and behavior. Follow precisely.
3. **Scope control**: Do NOT modify files not mentioned in your tasks.
4. **Mark progress**: After completing each task, mark it as `[x]` in `specs/016-phase7-native-parity-surface-and-conformance/tasks.md`.
5. **Commit convention**: Commit after each logical group with message format:
   `feat(016): T007–T012 safe domain margin-check and profit-calc`
6. **No speckit commands**: Speckit CLI is not available in this environment. Apply all changes manually.
7. **Preserve existing code**: Only ADD or MODIFY as specified — do not remove unrelated functionality.
8. **No placeholders**: Every task must produce working code, not TODO comments or stubs.
