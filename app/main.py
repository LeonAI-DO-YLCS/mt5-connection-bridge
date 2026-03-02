"""
MT5 Bridge — FastAPI application entrypoint.

Start with:
    uvicorn app.main:app --host 0.0.0.0 --port 8001
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .audit import init_audit_logging
from .auth import verify_api_key
from .config import Settings, load_symbol_map
from .metrics import RollingMetrics
from .mt5_worker import start_worker, stop_worker

logger = logging.getLogger("mt5_bridge")

settings = Settings()
symbol_map = load_symbol_map(settings.symbols_config_path)
metrics_store = RollingMetrics(retention_days=settings.metrics_retention_days)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s  %(name)-14s  %(levelname)-7s  %(message)s",
    )
    logger.info("Starting MT5 Bridge on port %d …", settings.mt5_bridge_port)
    logger.info("Loaded %d symbol mappings.", len(symbol_map))

    init_audit_logging()
    if not settings.disable_mt5_worker:
        start_worker(settings)
    yield
    if not settings.disable_mt5_worker:
        stop_worker()


app = FastAPI(
    title="MT5 Bridge",
    version="1.1.0",
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
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


from .routes.config_info import router as config_info_router  # noqa: E402
from .routes.execute import router as execute_router  # noqa: E402
from .routes.health import router as health_router  # noqa: E402
from .routes.logs import router as logs_router  # noqa: E402
from .routes.metrics import router as metrics_router  # noqa: E402
from .routes.prices import router as prices_router  # noqa: E402
from .routes.symbols import router as symbols_router  # noqa: E402
from .routes.worker import router as worker_router  # noqa: E402

app.include_router(health_router)
app.include_router(prices_router)
app.include_router(execute_router)
app.include_router(symbols_router)
app.include_router(logs_router)
app.include_router(config_info_router)
app.include_router(worker_router)
app.include_router(metrics_router)

_dashboard_dir = Path(__file__).resolve().parent.parent / "dashboard"
if _dashboard_dir.exists():
    app.mount("/dashboard", StaticFiles(directory=str(_dashboard_dir), html=True), name="dashboard")
