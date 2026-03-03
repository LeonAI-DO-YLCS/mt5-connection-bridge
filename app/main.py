"""
MT5 Bridge — FastAPI application entrypoint.

Start with:
    uvicorn app.main:app --host 0.0.0.0 --port 8001
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .audit import init_audit_logging
from .auth import verify_api_key
from .config import get_settings, load_symbol_map
from .metrics import RollingMetrics
from .mt5_worker import start_worker, stop_worker
from .runtime_state import apply_runtime_overrides

logger = logging.getLogger("mt5_bridge")

settings = get_settings()
symbol_map = load_symbol_map(settings.symbols_config_path)
metrics_store = RollingMetrics(retention_days=settings.metrics_retention_days)
app_version = "1.2.0"
app_started_at = datetime.now(timezone.utc)
runtime_policy_source = "env"


def get_runtime_policy_source() -> str:
    return runtime_policy_source


@asynccontextmanager
async def lifespan(app: FastAPI):
    global runtime_policy_source

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s  %(name)-14s  %(levelname)-7s  %(message)s",
    )
    runtime_policy_source = apply_runtime_overrides(settings)
    logger.info("Starting MT5 Bridge on port %d …", settings.mt5_bridge_port)
    logger.info("Loaded %d symbol mappings.", len(symbol_map))
    logger.info(
        "Execution policy source=%s enabled=%s",
        runtime_policy_source,
        settings.execution_enabled,
    )

    init_audit_logging(retention_days=settings.metrics_retention_days)
    if not settings.disable_mt5_worker:
        start_worker(settings)
    yield
    if not settings.disable_mt5_worker:
        stop_worker()


app = FastAPI(
    title="MT5 Bridge",
    version=app_version,
    description="Windows-native REST API bridge for MetaTrader 5",
    lifespan=lifespan,
    dependencies=[Depends(verify_api_key)],
)


@app.middleware("http")
async def request_metrics_middleware(request: Request, call_next):
    endpoint = request.url.path
    try:
        response = await call_next(request)
    except Exception:
        metrics_store.record_request(endpoint, 500)
        raise

    metrics_store.record_request(endpoint, response.status_code)
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers={"X-Error-Code": "INTERNAL_SERVER_ERROR"},
    )


def _infer_error_code(status_code: int, detail: object) -> str:
    text = str(detail).lower()
    if status_code == 401:
        return "UNAUTHORIZED_API_KEY"
    if status_code == 403 and "execution disabled" in text:
        return "EXECUTION_DISABLED"
    if status_code == 404 and "ticker" in text:
        return "SYMBOL_NOT_CONFIGURED"
    if status_code == 404 and "not found" in text:
        return "RESOURCE_NOT_FOUND"
    if status_code == 409:
        return "OVERLOAD_OR_SINGLE_FLIGHT"
    if status_code == 422:
        return "VALIDATION_ERROR"
    if status_code == 503 and ("not connected" in text or "terminal" in text):
        return "MT5_DISCONNECTED"
    if status_code == 503:
        return "SERVICE_UNAVAILABLE"
    if status_code >= 500:
        return "INTERNAL_SERVER_ERROR"
    return "REQUEST_ERROR"


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    headers = dict(exc.headers or {})
    headers.setdefault("X-Error-Code", _infer_error_code(exc.status_code, exc.detail))
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=headers)


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
        headers={"X-Error-Code": "VALIDATION_ERROR"},
    )


from .routes.config_info import router as config_info_router  # noqa: E402
from .routes.diagnostics import router as diagnostics_router  # noqa: E402
from .routes.execute import router as execute_router  # noqa: E402
from .routes.health import router as health_router  # noqa: E402
from .routes.logs import router as logs_router  # noqa: E402
from .routes.metrics import router as metrics_router  # noqa: E402
from .routes.prices import router as prices_router  # noqa: E402
from .routes.symbols import router as symbols_router  # noqa: E402
from .routes.worker import router as worker_router  # noqa: E402
from .routes.positions import router as positions_router  # noqa: E402
from .routes.orders import router as orders_router  # noqa: E402
from .routes.account import router as account_router  # noqa: E402
from .routes.tick import router as tick_router  # noqa: E402
from .routes.terminal import router as terminal_router  # noqa: E402
from .routes.history import router as history_router  # noqa: E402
from .routes.close_position import router as close_position_router  # noqa: E402
from .routes.pending_order import router as pending_order_router  # noqa: E402
from .routes.order_check import router as order_check_router  # noqa: E402
from .routes.broker_symbols import router as broker_symbols_router  # noqa: E402

app.include_router(health_router)
app.include_router(prices_router)
app.include_router(execute_router)
app.include_router(symbols_router)
app.include_router(logs_router)
app.include_router(config_info_router)
app.include_router(diagnostics_router)
app.include_router(worker_router)
app.include_router(metrics_router)
app.include_router(positions_router)
app.include_router(orders_router)
app.include_router(account_router)
app.include_router(tick_router)
app.include_router(terminal_router)
app.include_router(history_router)
app.include_router(close_position_router)
app.include_router(pending_order_router)
app.include_router(order_check_router)
app.include_router(broker_symbols_router)

_dashboard_dir = Path(__file__).resolve().parent.parent / "dashboard"
if _dashboard_dir.exists():
    app.mount("/dashboard", StaticFiles(directory=str(_dashboard_dir), html=True), name="dashboard")
