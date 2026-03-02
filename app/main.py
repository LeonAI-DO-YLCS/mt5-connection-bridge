"""
MT5 Bridge — FastAPI application entrypoint.

Start with:
    uvicorn app.main:app --host 0.0.0.0 --port 8001
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from .audit import init_audit_logging
from .auth import verify_api_key
from .config import Settings, load_symbol_map
from .mt5_worker import start_worker, stop_worker

logger = logging.getLogger("mt5_bridge")

# ---- Application-wide singletons ----
settings = Settings()
symbol_map = load_symbol_map()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle for the MT5 worker thread."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s  %(name)-14s  %(levelname)-7s  %(message)s",
    )
    logger.info("Starting MT5 Bridge on port %d …", settings.mt5_bridge_port)
    logger.info("Loaded %d symbol mappings.", len(symbol_map))

    init_audit_logging()
    start_worker(settings)
    yield
    stop_worker()


app = FastAPI(
    title="MT5 Bridge",
    version="1.0.0",
    description="Windows-native REST API bridge for MetaTrader 5",
    lifespan=lifespan,
    dependencies=[Depends(verify_api_key)],
)

# ---- Import and include routers ----
from .routes.health import router as health_router  # noqa: E402
from .routes.execute import router as execute_router  # noqa: E402
from .routes.prices import router as prices_router  # noqa: E402

app.include_router(health_router)
app.include_router(prices_router)
app.include_router(execute_router)
