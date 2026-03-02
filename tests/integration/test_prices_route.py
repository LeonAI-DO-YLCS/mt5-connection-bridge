from __future__ import annotations

from concurrent.futures import Future

import numpy as np

from app.mt5_worker import WorkerState


def _future(value):
    fut = Future()
    fut.set_result(value)
    return fut


def test_prices_unknown_ticker(client, auth_headers):
    response = client.get(
        "/prices?ticker=UNKNOWN&start_date=2026-01-01&end_date=2026-01-02&timeframe=D1",
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_prices_disconnected_returns_503(client, auth_headers, monkeypatch):
    from app.routes import prices as prices_route

    monkeypatch.setattr(prices_route, "get_state", lambda: WorkerState.DISCONNECTED)

    response = client.get(
        "/prices?ticker=V75&start_date=2026-01-01&end_date=2026-01-02&timeframe=D1",
        headers=auth_headers,
    )
    assert response.status_code == 503


def test_prices_success(client, auth_headers, monkeypatch):
    from app.routes import prices as prices_route

    rates = np.array(
        [(1704067200, 10.0, 12.0, 9.0, 11.0, 10, 0, 0)],
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

    monkeypatch.setattr(prices_route, "get_state", lambda: WorkerState.AUTHORIZED)
    monkeypatch.setattr(prices_route, "submit", lambda fn: _future(rates))

    response = client.get(
        "/prices?ticker=V75&start_date=2026-01-01&end_date=2026-01-02&timeframe=D1",
        headers=auth_headers,
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["ticker"] == "V75"
    assert len(payload["prices"]) == 1
