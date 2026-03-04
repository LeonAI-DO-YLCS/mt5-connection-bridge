from __future__ import annotations

import json
import os
import sys
import types
from concurrent.futures import Future
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DISABLE_MT5_WORKER", "true")
os.environ.setdefault("MT5_BRIDGE_API_KEY", "test-api-key")
os.environ.setdefault("EXECUTION_ENABLED", "false")
os.environ.setdefault("METRICS_RETENTION_DAYS", "90")
os.environ.setdefault("MULTI_TRADE_OVERLOAD_QUEUE_THRESHOLD", "100")
os.environ.setdefault("STRICT_HTTP_SEMANTICS", "true")


@pytest.fixture
def fake_mt5(monkeypatch):
    module = types.ModuleType("MetaTrader5")

    module.ORDER_TYPE_BUY = 0
    module.ORDER_TYPE_SELL = 1
    module.TRADE_ACTION_DEAL = 1
    module.ORDER_TIME_GTC = 0
    module.ORDER_FILLING_IOC = 2
    module.TRADE_RETCODE_DONE = 10009

    module._last_error = (0, "ok")
    module._tick = SimpleNamespace(bid=100.0, ask=100.1)
    module._symbol_info = SimpleNamespace(visible=True, volume_min=0.01, volume_max=100.0, volume_step=0.01, spread=10)
    module._order_result = SimpleNamespace(retcode=10009, price=100.1, volume=0.01, order=12345, comment="done")
    module._rates = np.array(
        [
            (1704067200, 100.0, 102.0, 99.0, 101.0, 11, 0, 0),
            (1704153600, 101.0, 103.0, 100.0, 102.0, 12, 0, 0),
        ],
        dtype=[
            ("time", "i8"),
            ("open", "f8"),
            ("high", "f8"),
            ("low", "f8"),
            ("close", "f8"),
            ("tick_volume", "i8"),
            ("spread", "i8"),
            ("real_volume", "i8"),
        ],
    )

    def initialize(**kwargs):
        return True

    def login(**kwargs):
        return True

    def shutdown():
        return True

    def last_error():
        return module._last_error

    def account_info():
        return SimpleNamespace(company="Deriv", login=987654, balance=1000.0, server_time=1704067200)

    def copy_rates_range(symbol, timeframe, start, end):
        return module._rates

    def symbol_info(symbol):
        return module._symbol_info

    def symbol_select(symbol, visible):
        return True

    def symbol_info_tick(symbol):
        return module._tick

    def order_send(request):
        return module._order_result

    module.initialize = initialize
    module.login = login
    module.shutdown = shutdown
    module.last_error = last_error
    module.account_info = account_info
    module.copy_rates_range = copy_rates_range
    module.symbol_info = symbol_info
    module.symbol_select = symbol_select
    module.symbol_info_tick = symbol_info_tick
    module.order_send = order_send

    monkeypatch.setitem(sys.modules, "MetaTrader5", module)
    return module


@pytest.fixture
def client(monkeypatch, tmp_path, fake_mt5):
    from app import audit
    from app.main import app, metrics_store, settings

    settings.mt5_bridge_api_key = "test-api-key"
    settings.execution_enabled = False
    settings.metrics_retention_days = 90
    settings.multi_trade_overload_queue_threshold = 100
    settings.max_pre_dispatch_slippage_pct = 1.0
    settings.max_post_fill_slippage_pct = 1.0

    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    settings.runtime_state_path = str(logs_dir / "runtime_state.json")
    monkeypatch.setattr(audit, "_LOG_DIR", logs_dir)

    metrics_store.log_path = logs_dir / "metrics.jsonl"
    metrics_store.retention_days = 90
    metrics_store.reset()

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers():
    return {"X-API-KEY": "test-api-key"}


@pytest.fixture
def completed_future_factory():
    def _factory(value=None, error: Exception | None = None):
        fut = Future()
        if error is not None:
            fut.set_exception(error)
        else:
            fut.set_result(value)
        return fut

    return _factory


@pytest.fixture
def immediate_submit(monkeypatch):
    from app.routes import execute as execute_route
    from app.routes import prices as prices_route

    def _submit(fn):
        fut = Future()
        try:
            fut.set_result(fn())
        except Exception as exc:
            fut.set_exception(exc)
        return fut

    monkeypatch.setattr(prices_route, "submit", _submit)
    monkeypatch.setattr(execute_route, "submit", _submit)
    return _submit


@pytest.fixture
def write_trade_logs(tmp_path):
    def _writer(count: int) -> Path:
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        path = logs_dir / "trades.jsonl"
        with path.open("w", encoding="utf-8") as fh:
            for i in range(count):
                entry = {
                    "timestamp": f"2026-03-02T00:00:{i % 60:02d}+00:00",
                    "request": {"ticker": "V75", "action": "buy", "quantity": 0.01, "current_price": 1000.0},
                    "response": {"success": True, "ticket_id": i},
                    "metadata": {"state": "fill_confirmed"},
                }
                fh.write(json.dumps(entry) + "\n")
        return path

    return _writer


@pytest.fixture(autouse=True)
def reset_execute_state():
    from app.main import settings
    from app.routes import execute as execute_route

    settings.execution_enabled = False
    settings.multi_trade_overload_queue_threshold = 100
    settings.max_pre_dispatch_slippage_pct = 1.0
    settings.max_post_fill_slippage_pct = 1.0
    execute_route._inflight_requests = 0
    yield
    execute_route._inflight_requests = 0


def pytest_collection_modifyitems(config, items):
    smoke_files = {
        "tests/unit/test_auth.py",
        "tests/integration/test_health_route.py",
        "tests/integration/test_config_route.py",
        "tests/integration/test_symbols_route.py",
        "tests/integration/test_tick_route.py",
    }
    for item in items:
        path = str(item.fspath).replace("\\", "/")
        if "/tests/unit/" in path:
            item.add_marker(pytest.mark.unit)
        elif "/tests/integration/" in path:
            item.add_marker(pytest.mark.integration)
        elif "/tests/contract/" in path:
            item.add_marker(pytest.mark.contract)
        elif "/tests/performance/" in path:
            item.add_marker(pytest.mark.performance)

        for suffix in smoke_files:
            if path.endswith(suffix):
                item.add_marker(pytest.mark.smoke)
                break
