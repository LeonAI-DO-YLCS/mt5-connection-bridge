from __future__ import annotations

from app.models.trade import TradeRequest, TradeResponse


def test_logs_empty_state(client, auth_headers):
    response = client.get("/logs?limit=20&offset=0", headers=auth_headers)
    payload = response.json()

    assert response.status_code == 200
    assert payload["total"] == 0
    assert payload["entries"] == []


def test_logs_pagination(client, auth_headers):
    from app.audit import log_trade

    for idx in range(3):
        req = TradeRequest(
            ticker="V75", action="buy", quantity=0.01, current_price=100.0
        )
        res = TradeResponse(success=True, ticket_id=idx)
        log_trade(req, res, metadata={"state": "fill_confirmed"})

    response = client.get("/logs?limit=2&offset=1", headers=auth_headers)
    payload = response.json()

    assert response.status_code == 200
    assert payload["total"] == 3
    assert payload["limit"] == 2
    assert len(payload["entries"]) == 2
    assert payload["entries"][0]["outcome"] == "success"
    assert payload["entries"][0]["metadata"]["state"] == "fill_confirmed"
