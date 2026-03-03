"""T030: Contract tests — canonical envelope fields on trade-affecting endpoints.

Every error response from trade-affecting endpoints MUST contain:
  ok, category, code, tracking_id, title, message, action, severity, retryable, context, detail
"""
from __future__ import annotations

import pytest

# All 6 trade-affecting endpoint families. execution_enabled=False in conftest,
# so these will all return an error (403) with the canonical envelope shape.

ENVELOPE_REQUIRED_KEYS = {
    "ok", "category", "code", "tracking_id", "title",
    "message", "action", "severity", "retryable", "context", "detail",
}


class TestCanonicalEnvelopeContract:
    """Every trade-affecting error response must include all canonical envelope fields."""

    def test_execute_returns_envelope(self, client, auth_headers):
        resp = client.post(
            "/execute",
            json={"ticker": "V75", "action": "buy", "quantity": 0.01, "current_price": 100.0},
            headers=auth_headers,
        )
        assert resp.status_code == 403
        body = resp.json()
        missing = ENVELOPE_REQUIRED_KEYS - body.keys()
        assert not missing, f"Missing keys in /execute envelope: {missing}"
        assert body["ok"] is False
        assert body["code"] == "EXECUTION_DISABLED"

    def test_close_position_returns_envelope(self, client, auth_headers):
        resp = client.post(
            "/close-position",
            json={"ticket": 123456},
            headers=auth_headers,
        )
        assert resp.status_code == 403
        body = resp.json()
        missing = ENVELOPE_REQUIRED_KEYS - body.keys()
        assert not missing, f"Missing keys in /close-position envelope: {missing}"
        assert body["ok"] is False

    def test_pending_order_returns_envelope(self, client, auth_headers):
        resp = client.post(
            "/pending-order",
            json={
                "ticker": "V75", "type": "buy_limit", "volume": 0.01,
                "price": 100.0, "sl": 0, "tp": 0, "comment": "",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 403
        body = resp.json()
        missing = ENVELOPE_REQUIRED_KEYS - body.keys()
        assert not missing, f"Missing keys in /pending-order envelope: {missing}"
        assert body["ok"] is False

    def test_cancel_order_returns_envelope(self, client, auth_headers):
        resp = client.delete("/orders/99999", headers=auth_headers)
        assert resp.status_code == 403
        body = resp.json()
        missing = ENVELOPE_REQUIRED_KEYS - body.keys()
        assert not missing, f"Missing keys in DELETE /orders/99999 envelope: {missing}"
        assert body["ok"] is False

    def test_modify_order_returns_envelope(self, client, auth_headers):
        resp = client.put(
            "/orders/99999",
            json={"price": 100.0, "sl": 0, "tp": 0},
            headers=auth_headers,
        )
        assert resp.status_code == 403
        body = resp.json()
        missing = ENVELOPE_REQUIRED_KEYS - body.keys()
        assert not missing, f"Missing keys in PUT /orders/99999 envelope: {missing}"
        assert body["ok"] is False

    def test_modify_sltp_returns_envelope(self, client, auth_headers):
        resp = client.put(
            "/positions/99999/sltp",
            json={"sl": 0, "tp": 0},
            headers=auth_headers,
        )
        assert resp.status_code == 403
        body = resp.json()
        missing = ENVELOPE_REQUIRED_KEYS - body.keys()
        assert not missing, f"Missing keys in PUT /positions/99999/sltp envelope: {missing}"
        assert body["ok"] is False

    def test_envelope_has_tracking_id_header(self, client, auth_headers):
        resp = client.post(
            "/execute",
            json={"ticker": "V75", "action": "buy", "quantity": 0.01, "current_price": 100.0},
            headers=auth_headers,
        )
        assert "x-tracking-id" in resp.headers
        assert resp.headers["x-tracking-id"].startswith("brg-")

    def test_envelope_has_error_code_header(self, client, auth_headers):
        resp = client.post(
            "/execute",
            json={"ticker": "V75", "action": "buy", "quantity": 0.01, "current_price": 100.0},
            headers=auth_headers,
        )
        assert "x-error-code" in resp.headers
        assert resp.headers["x-error-code"] == "EXECUTION_DISABLED"
