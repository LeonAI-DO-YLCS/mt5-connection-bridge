"""T029: Contract tests — backward compatibility of legacy `detail` field.

The `detail` field MUST still be present in all error responses during the
migration window (Phases 1–5) so existing API consumers are not broken.
"""
from __future__ import annotations

import pytest


class TestBackwardCompatibility:
    """Legacy `detail` field is present in error responses alongside the canonical envelope."""

    def test_execute_has_detail(self, client, auth_headers):
        resp = client.post(
            "/execute",
            json={"ticker": "V75", "action": "buy", "quantity": 0.01, "current_price": 100.0},
            headers=auth_headers,
        )
        body = resp.json()
        assert "detail" in body, "detail field missing for backward compat"
        assert body["detail"] is not None

    def test_close_position_has_detail(self, client, auth_headers):
        resp = client.post(
            "/close-position",
            json={"ticket": 123456},
            headers=auth_headers,
        )
        body = resp.json()
        assert "detail" in body, "detail field missing for backward compat"
        assert body["detail"] is not None

    def test_pending_order_has_detail(self, client, auth_headers):
        resp = client.post(
            "/pending-order",
            json={
                "ticker": "V75", "type": "buy_limit", "volume": 0.01,
                "price": 100.0, "sl": 0, "tp": 0, "comment": "",
            },
            headers=auth_headers,
        )
        body = resp.json()
        assert "detail" in body, "detail field missing for backward compat"
        assert body["detail"] is not None

    def test_cancel_order_has_detail(self, client, auth_headers):
        resp = client.delete("/orders/99999", headers=auth_headers)
        body = resp.json()
        assert "detail" in body, "detail field missing for backward compat"
        assert body["detail"] is not None

    def test_modify_order_has_detail(self, client, auth_headers):
        resp = client.put(
            "/orders/99999",
            json={"price": 100.0, "sl": 0, "tp": 0},
            headers=auth_headers,
        )
        body = resp.json()
        assert "detail" in body, "detail field missing for backward compat"
        assert body["detail"] is not None

    def test_modify_sltp_has_detail(self, client, auth_headers):
        resp = client.put(
            "/positions/99999/sltp",
            json={"sl": 0, "tp": 0},
            headers=auth_headers,
        )
        body = resp.json()
        assert "detail" in body, "detail field missing for backward compat"
        assert body["detail"] is not None

    def test_validation_error_has_detail_as_list(self, client, auth_headers):
        """Pydantic validation errors produce detail as a list (legacy format)."""
        resp = client.post(
            "/execute",
            json={},  # Missing required fields
            headers=auth_headers,
        )
        assert resp.status_code == 422
        body = resp.json()
        assert "detail" in body, "detail field missing for validation errors"
        assert isinstance(body["detail"], list), "Validation detail should be a list"

    def test_x_error_code_header_preserved(self, client, auth_headers):
        """X-Error-Code header must still be populated and map to canonical code."""
        resp = client.post(
            "/execute",
            json={"ticker": "V75", "action": "buy", "quantity": 0.01, "current_price": 100.0},
            headers=auth_headers,
        )
        assert "x-error-code" in resp.headers
        body = resp.json()
        assert resp.headers["x-error-code"] == body["code"]
