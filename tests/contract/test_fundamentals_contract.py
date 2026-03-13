"""Contract tests for MT5 Bridge fundamentals endpoints."""

from unittest.mock import patch


def _financial_metric_payload():
    return {
        "ticker": "AAPL",
        "report_period": "2025-12-31",
        "period": "ttm",
        "currency": "USD",
        "market_cap": 1000.0,
        "enterprise_value": None,
        "price_to_earnings_ratio": None,
        "price_to_book_ratio": None,
        "price_to_sales_ratio": None,
        "enterprise_value_to_ebitda_ratio": None,
        "enterprise_value_to_revenue_ratio": None,
        "free_cash_flow_yield": None,
        "peg_ratio": None,
        "gross_margin": None,
        "operating_margin": None,
        "net_margin": None,
        "return_on_equity": None,
        "return_on_assets": None,
        "return_on_invested_capital": None,
        "asset_turnover": None,
        "inventory_turnover": None,
        "receivables_turnover": None,
        "days_sales_outstanding": None,
        "operating_cycle": None,
        "working_capital_turnover": None,
        "current_ratio": None,
        "quick_ratio": None,
        "cash_ratio": None,
        "operating_cash_flow_ratio": None,
        "debt_to_equity": None,
        "debt_to_assets": None,
        "interest_coverage": None,
        "revenue_growth": None,
        "earnings_growth": None,
        "book_value_growth": None,
        "earnings_per_share_growth": None,
        "free_cash_flow_growth": None,
        "operating_income_growth": None,
        "ebitda_growth": None,
        "payout_ratio": None,
        "earnings_per_share": None,
        "book_value_per_share": None,
        "free_cash_flow_per_share": None,
    }


class TestFundamentalsContract:
    def test_financial_metrics_mt5_native_empty(self, client, auth_headers):
        resp = client.get(
            "/financial-metrics?ticker=V75&end_date=2026-01-01", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json() == {"financial_metrics": []}

    @patch("requests.get")
    def test_financial_metrics_equity_proxy(self, mock_get, client, auth_headers):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "financial_metrics": [_financial_metric_payload()]
        }

        resp = client.get(
            "/financial-metrics?ticker=AAPL&end_date=2026-01-01", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["financial_metrics"][0]["ticker"] == "AAPL"
        assert data["financial_metrics"][0]["report_period"] == "2025-12-31"

    def test_line_items_search_mt5_native_empty(self, client, auth_headers):
        resp = client.post(
            "/line-items/search", json={"tickers": ["V75"]}, headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json() == {"search_results": []}

    @patch("requests.post")
    def test_line_items_search_equity_proxy(self, mock_post, client, auth_headers):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "search_results": [
                {
                    "ticker": "AAPL",
                    "report_period": "2025-12-31",
                    "period": "ttm",
                    "currency": "USD",
                    "revenue": 5,
                }
            ]
        }

        resp = client.post(
            "/line-items/search", json={"tickers": ["AAPL"]}, headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["search_results"][0]["ticker"] == "AAPL"

    def test_insider_trades_mt5_native_empty(self, client, auth_headers):
        resp = client.get(
            "/insider-trades?ticker=V75&end_date=2026-01-01", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json() == {"insider_trades": []}

    @patch("requests.get")
    def test_insider_trades_equity_proxy(self, mock_get, client, auth_headers):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "insider_trades": [
                {
                    "ticker": "AAPL",
                    "issuer": None,
                    "name": None,
                    "title": None,
                    "is_board_director": None,
                    "transaction_date": None,
                    "transaction_shares": None,
                    "transaction_price_per_share": None,
                    "transaction_value": None,
                    "shares_owned_before_transaction": None,
                    "shares_owned_after_transaction": None,
                    "security_title": None,
                    "filing_date": "2026-01-01",
                }
            ]
        }

        resp = client.get(
            "/insider-trades?ticker=AAPL&end_date=2026-01-01", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["insider_trades"][0]["ticker"] == "AAPL"

    def test_company_news_mt5_native_empty(self, client, auth_headers):
        resp = client.get(
            "/company-news?ticker=EURUSD&end_date=2026-01-01", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json() == {"news": []}

    @patch("requests.get")
    def test_company_news_equity_proxy(self, mock_get, client, auth_headers):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "news": [
                {
                    "ticker": "AAPL",
                    "title": "News",
                    "author": "Reporter",
                    "source": "Wire",
                    "date": "2026-01-01",
                    "url": "https://example.com",
                }
            ]
        }

        resp = client.get(
            "/company-news?ticker=AAPL&end_date=2026-01-01", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["news"][0]["ticker"] == "AAPL"

    def test_company_facts_mt5_native_default_identity(self, client, auth_headers):
        resp = client.get("/company-facts?ticker=EURUSD", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["company_facts"] == {
            "ticker": "EURUSD",
            "name": "EURUSD",
            "cik": None,
            "industry": None,
            "sector": None,
            "category": None,
            "exchange": None,
            "is_active": None,
            "listing_date": None,
            "location": None,
            "market_cap": None,
            "number_of_employees": None,
            "sec_filings_url": None,
            "sic_code": None,
            "sic_industry": None,
            "sic_sector": None,
            "website_url": None,
            "weighted_average_shares": None,
        }

    @patch("requests.get")
    def test_company_facts_equity_proxy(self, mock_get, client, auth_headers):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "company_facts": {"ticker": "AAPL", "name": "Apple", "market_cap": 1e12}
        }

        resp = client.get("/company-facts?ticker=AAPL", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["company_facts"]["name"] == "Apple"
