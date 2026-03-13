"""
T018 — Bridge execution fill integration tests.

Covers fractional-lot fills, partial fills, and disconnected-terminal scenarios
for the MT5 Bridge execution path.
"""
from __future__ import annotations

from app.mt5_worker import WorkerState


FRACTIONAL_PAYLOAD = {
    "ticker": "V75",
    "action": "buy",
    "quantity": 0.01,
    "current_price": 50000.0,
}


def test_fractional_fill_precision(client, auth_headers, monkeypatch, fake_mt5, immediate_submit):
    """T018-1: Fractional lot fills preserve precision without truncation."""
    from app.main import settings
    from app.routes import execute as execute_route

    settings.execution_enabled = True
    settings.max_pre_dispatch_slippage_pct = 99.0
    settings.max_post_fill_slippage_pct = 99.0
    fake_mt5._tick.ask = 50000.0
    fake_mt5._order_result.price = 50005.0
    fake_mt5._order_result.volume = 0.01  # fractional lot

    monkeypatch.setattr(execute_route, "get_state", lambda: WorkerState.AUTHORIZED)

    response = client.post("/execute", headers=auth_headers, json=FRACTIONAL_PAYLOAD)
    payload = response.json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["filled_quantity"] == 0.01
    assert isinstance(payload["filled_price"], float)
    assert payload["filled_price"] > 0


def test_partial_fill_response(client, auth_headers, monkeypatch, fake_mt5, immediate_submit):
    """T018-2: Partial fills report the actual filled quantity, not the requested quantity."""
    from app.main import settings
    from app.routes import execute as execute_route

    settings.execution_enabled = True
    settings.max_pre_dispatch_slippage_pct = 99.0
    settings.max_post_fill_slippage_pct = 99.0
    fake_mt5._tick.ask = 50000.0
    fake_mt5._order_result.price = 50000.0
    fake_mt5._order_result.volume = 0.005  # partial: wanted 0.01, got 0.005

    monkeypatch.setattr(execute_route, "get_state", lambda: WorkerState.AUTHORIZED)

    payload_req = dict(FRACTIONAL_PAYLOAD)
    payload_req["quantity"] = 0.01

    response = client.post("/execute", headers=auth_headers, json=payload_req)
    payload = response.json()

    assert response.status_code == 200
    assert payload["success"] is True
    # The filled_quantity should match the volume actually reported by MT5
    assert payload["filled_quantity"] == 0.005


def test_disconnected_terminal_safe_error(client, auth_headers, monkeypatch, immediate_submit):
    """T018-3: Disconnected MT5 terminal returns safe error response."""
    from app.routes import execute as execute_route

    from app.main import settings
    settings.execution_enabled = True

    monkeypatch.setattr(execute_route, "get_state", lambda: WorkerState.DISCONNECTED)

    response = client.post("/execute", headers=auth_headers, json=FRACTIONAL_PAYLOAD)
    payload = response.json()

    assert response.status_code == 503
    assert "MT5_DISCONNECTED" == payload.get("code")
