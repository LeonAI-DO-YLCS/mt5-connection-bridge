"""Integration tests for compatibility middleware (T013)."""

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _compat_mode():
    """Ensure compat mode by default, each test may override."""
    original = os.environ.get("STRICT_HTTP_SEMANTICS")
    os.environ["STRICT_HTTP_SEMANTICS"] = "false"
    yield
    if original is None:
        os.environ.pop("STRICT_HTTP_SEMANTICS", None)
    else:
        os.environ["STRICT_HTTP_SEMANTICS"] = original


@pytest.fixture
def client():
    """Create a test client with MT5 worker disabled."""
    os.environ["MT5_BRIDGE_API_KEY"] = "test-key"
    os.environ["DISABLE_MT5_WORKER"] = "true"
    os.environ["EXECUTION_ENABLED"] = "false"

    from app.config import get_settings
    get_settings.cache_clear()

    # Reload the auth module so _settings picks up the new key
    import importlib
    import app.auth
    importlib.reload(app.auth)

    from app.main import app

    return TestClient(app, headers={"X-API-KEY": "test-key"})


class TestCompatMiddleware:
    def test_compat_mode_rewrites_403_to_200(self, client):
        """In compat mode, a 403 from /execute should become 200 with deprecation headers."""
        response = client.post("/execute", json={
            "ticker": "AAPL", "action": "buy", "quantity": 0.01, "current_price": 100.0,
            "mt5_symbol_direct": "AAPL.raw",
        })
        # The endpoint raises EXECUTION_DISABLED (403) which compat rewrites to 200
        assert response.status_code == 200
        assert response.headers.get("Deprecation") == "true"
        assert response.headers.get("X-Original-Status") == "403"

    def test_strict_mode_preserves_403(self, client):
        """In strict mode, a 403 should remain 403."""
        os.environ["STRICT_HTTP_SEMANTICS"] = "true"
        response = client.post("/execute", json={
            "ticker": "AAPL", "action": "buy", "quantity": 0.01, "current_price": 100.0,
            "mt5_symbol_direct": "AAPL.raw",
        })
        assert response.status_code == 403
        assert "Deprecation" not in response.headers

    def test_non_trade_routes_unaffected(self, client):
        """Non-trade routes should never be rewritten."""
        response = client.get("/health")
        assert response.status_code == 200
