"""
T012: Contract tests for MT5 Bridge fundamentals endpoints.

These endpoints must return empty arrays for MT5-native instruments (e.g., V75),
and optionally proxy to external data sources for equities (e.g., AAPL).
"""
import pytest
from unittest.mock import patch


class TestFundamentalsContract:
    def test_financial_metrics_mt5_native_empty(self, client, auth_headers):
        resp = client.get("/financial-metrics?ticker=V75&end_date=2026-01-01", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "financial_metrics" in data
        assert data["financial_metrics"] == []

    @patch("requests.get")
    def test_financial_metrics_equity_proxy(self, mock_get, client, auth_headers):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"financial_metrics": [{"revenue": 500}]}

        resp = client.get("/financial-metrics?ticker=AAPL&end_date=2026-01-01", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "financial_metrics" in data
        assert len(data["financial_metrics"]) == 1
        assert data["financial_metrics"][0]["revenue"] == 500
        mock_get.assert_called_once()

    def test_line_items_search_mt5_native_empty(self, client, auth_headers):
        resp = client.post("/line-items/search", json={"tickers": ["V75"]}, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "search_results" in data
        assert data["search_results"] == []

    @patch("requests.post")
    def test_line_items_search_equity_proxy(self, mock_post, client, auth_headers):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"search_results": [{"item": "val"}]}

        resp = client.post("/line-items/search", json={"tickers": ["AAPL"]}, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "search_results" in data
        assert len(data["search_results"]) == 1
        mock_post.assert_called_once()

    def test_insider_trades_mt5_native_empty(self, client, auth_headers):
        resp = client.get("/insider-trades?ticker=V75&end_date=2026-01-01", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "insider_trades" in data
        assert data["insider_trades"] == []

    @patch("requests.get")
    def test_insider_trades_equity_proxy(self, mock_get, client, auth_headers):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"insider_trades": [{"trade": "info"}]}

        resp = client.get("/insider-trades?ticker=AAPL&end_date=2026-01-01", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "insider_trades" in data
        assert len(data["insider_trades"]) == 1
        mock_get.assert_called_once()

    def test_company_news_mt5_native_empty(self, client, auth_headers):
        resp = client.get("/company-news?ticker=EURUSD&end_date=2026-01-01", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "news" in data
        assert data["news"] == []

    @patch("requests.get")
    def test_company_news_equity_proxy(self, mock_get, client, auth_headers):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"news": [{"title": "News"}]}

        resp = client.get("/company-news?ticker=AAPL&end_date=2026-01-01", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "news" in data
        assert len(data["news"]) == 1
        mock_get.assert_called_once()

    def test_company_facts_mt5_native_empty(self, client, auth_headers):
        resp = client.get("/company-facts?ticker=EURUSD", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "company_facts" in data
        assert data["company_facts"].get("ticker") == "EURUSD"

    @patch("requests.get")
    def test_company_facts_equity_proxy(self, mock_get, client, auth_headers):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"company_facts": {"ticker": "AAPL", "market_cap": 1e12}}

        resp = client.get("/company-facts?ticker=AAPL", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "company_facts" in data
        assert data["company_facts"]["market_cap"] == 1e12
        mock_get.assert_called_once()
