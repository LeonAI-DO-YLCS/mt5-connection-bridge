## Context — Phase 7: Native Parity Surface and Conformance

You are implementing **Phase 7 — Native Parity Surface and Conformance** for the **MT5 Connection Bridge** project.
Branch: `016-phase7-native-parity-surface-and-conformance`

### Required Reading (READ BEFORE WRITING CODE)

Read these files in the repository for full context:

- `specs/016-phase7-native-parity-surface-and-conformance/tasks.md` — your task list (execute ONLY the tasks listed below)
- `specs/016-phase7-native-parity-surface-and-conformance/plan.md` — architecture, tech stack, project structure
- `specs/016-phase7-native-parity-surface-and-conformance/data-model.md` — MarketBookEntry model
- `specs/016-phase7-native-parity-surface-and-conformance/contracts/api-contracts.md` — API contracts for /mt5/raw/\* namespace
- `specs/016-phase7-native-parity-surface-and-conformance/research.md` — expert namespace design pattern (§2)
- `app/routes/__init__.py` — existing router registration pattern
- `app/mt5_worker.py` — worker `submit()` function for MT5 calls
- `app/auth.py` — `api_key_dependency` for route authentication

### Your Tasks — Phase 3: US2 — Expert/Advanced Namespace

Execute ONLY these tasks from `specs/016-phase7-native-parity-surface-and-conformance/tasks.md`:

- [ ] T013 [P] [US2] Create `MarketBookEntry` Pydantic model in `app/models/market_book.py` per data-model.md
- [ ] T014 [US2] Create expert namespace router in `app/routes/raw_namespace.py`:
  - FastAPI `APIRouter(prefix="/mt5/raw", tags=["advanced"])` with `api_key_dependency`
  - `GET /margin-check` — query params `symbol`, `volume`, `action`; calls `mt5.order_calc_margin()` via worker; response includes `namespace`, `safety_disclaimer`
  - `GET /profit-calc` — query params `symbol`, `volume`, `action`, `price_open`, `price_close`; calls `mt5.order_calc_profit()` via worker
  - `GET /market-book` — query param `symbol`; calls `mt5.market_book_add()`, `mt5.market_book_get()`, `mt5.market_book_release()` via worker; returns list of `MarketBookEntry`
  - `GET /terminal-info` — calls `mt5.terminal_info()` via worker; returns all fields (not curated)
  - `GET /account-info` — calls `mt5.account_info()` via worker; returns all fields
  - `GET /last-error` — calls `mt5.last_error()` via worker; returns raw error tuple
- [ ] T015 [US2] Register `raw_namespace_router` in `app/routes/__init__.py` and mount in the FastAPI app
- [ ] T016 [US2] Write unit tests for raw namespace in `tests/unit/test_raw_namespace.py` — mock MT5 functions, verify `namespace` and `safety_disclaimer` fields present in all responses, verify auth required, verify market-book lifecycle

### Rules

1. **Read first**: Read every file you are about to modify BEFORE making changes.
2. **Follow exactly**: Each task specifies the exact file, function, and behavior. Follow precisely.
3. **Scope control**: Do NOT modify files not mentioned in your tasks.
4. **Mark progress**: After completing each task, mark it as `[x]` in `specs/016-phase7-native-parity-surface-and-conformance/tasks.md`.
5. **Commit convention**: Commit after each logical group with message format:
   `feat(016): T013–T016 expert namespace /mt5/raw/* endpoints`
6. **No speckit commands**: Speckit CLI is not available in this environment. Apply all changes manually.
7. **Preserve existing code**: Only ADD or MODIFY as specified — do not remove unrelated functionality.
8. **No placeholders**: Every task must produce working code, not TODO comments or stubs.
