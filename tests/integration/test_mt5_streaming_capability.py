from __future__ import annotations

from concurrent.futures import Future

import numpy as np

from app.mt5_worker import WorkerState


def _future(value):
    fut = Future()
    fut.set_result(value)
    return fut


def test_prices_supports_m1_streaming_shape(client, auth_headers, monkeypatch):
    from app.routes import prices as prices_route

    rates = np.array(
        [(1704067200, 1.0, 2.0, 0.5, 1.5, 2, 0, 0)],
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
        "/prices?ticker=V75&start_date=2026-01-01&end_date=2026-01-02&timeframe=M1",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert len(response.json()["prices"]) == 1


def test_prices_supports_d1_streaming_shape(client, auth_headers, monkeypatch):
    from app.routes import prices as prices_route

    rates = np.array(
        [(1704067200, 10.0, 12.0, 8.0, 11.0, 3, 0, 0)],
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
    assert response.status_code == 200
    assert response.json()["ticker"] == "V75"
