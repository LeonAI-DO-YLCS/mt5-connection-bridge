from __future__ import annotations

import statistics
import time

from app.models.trade import TradeRequest, TradeResponse


def test_logs_pagination_median_under_2s_for_1000_entries(client, auth_headers):
    from app.audit import log_trade

    for idx in range(1000):
        req = TradeRequest(ticker="V75", action="buy", quantity=0.01, current_price=100.0)
        res = TradeResponse(success=True, ticket_id=idx)
        log_trade(req, res)

    durations = []
    for _ in range(5):
        start = time.perf_counter()
        resp = client.get("/logs?limit=100&offset=0", headers=auth_headers)
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        durations.append(elapsed)

    assert statistics.median(durations) <= 2.0
