"""Integration tests for the GET /readiness endpoint."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.models.readiness import OverallStatus, ReadinessStatus
from app.mt5_worker import WorkerState


class TestReadinessRoute:
    """Integration tests hitting the actual route via TestClient."""

    def test_global_only_returns_200(self, client, auth_headers, monkeypatch):
        """GET /readiness → 200 with global checks."""
        from app.services import readiness as svc

        monkeypatch.setattr(svc, "get_state", lambda: WorkerState.DISCONNECTED)

        resp = client.get("/readiness", headers=auth_headers)
        assert resp.status_code == 200

        body = resp.json()
        assert body["overall_status"] in ("ready", "degraded", "blocked")
        assert "checks" in body
        assert "blockers" in body
        assert "warnings" in body
        assert "evaluated_at" in body
        assert "request_context" in body

    def test_with_symbol_returns_200(self, client, auth_headers, monkeypatch):
        """GET /readiness?symbol=EURUSD → 200 with global + symbol checks."""
        from app.services import readiness as svc

        monkeypatch.setattr(svc, "get_state", lambda: WorkerState.DISCONNECTED)

        resp = client.get("/readiness?symbol=EURUSD", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["request_context"]["symbol"] == "EURUSD"

    def test_invalid_direction_returns_422(self, client, auth_headers):
        """GET /readiness?direction=invalid → 422 validation error."""
        resp = client.get("/readiness?direction=invalid", headers=auth_headers)
        assert resp.status_code == 422

    def test_negative_volume_returns_422(self, client, auth_headers):
        """GET /readiness?volume=-1 → 422 validation error."""
        resp = client.get("/readiness?volume=-1", headers=auth_headers)
        assert resp.status_code == 422

    def test_worker_disconnected_returns_blocked(self, client, auth_headers, monkeypatch):
        """When worker is disconnected → response is blocked."""
        from app.services import readiness as svc

        monkeypatch.setattr(svc, "get_state", lambda: WorkerState.DISCONNECTED)

        resp = client.get("/readiness", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["overall_status"] == "blocked"
        assert any(b["check_id"] == "global.worker_connected" for b in body["blockers"])

    def test_requires_api_key(self, client):
        """GET /readiness without API key → 401."""
        resp = client.get("/readiness")
        assert resp.status_code == 401
