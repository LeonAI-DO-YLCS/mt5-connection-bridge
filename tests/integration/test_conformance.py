import pytest
import json
import os
from unittest.mock import patch
import httpx

from app.conformance.runner import ConformanceRunner
from app.conformance.reporter import ConformanceReporter

@pytest.fixture
def mock_httpx_client():
    class MockResponse:
        def __init__(self, status_code, json_data=None, text=""):
            self.status_code = status_code
            self._json_data = json_data
            self.text = text
            
        def json(self):
            if self._json_data is not None:
                return self._json_data
            raise ValueError("No JSON data")

    class MockAsyncClient:
        def __init__(self, **kwargs):
            pass
            
        async def get(self, url, **kwargs):
            if "/diagnostics/runtime" in url:
                return MockResponse(200, {
                    "terminal": {"company": "Test Broker", "server": "Test Server", "build": "3802"},
                    "runtime": {"python_version": "3.10.12"},
                    "compatibility_profile": {"name": "balanced"}
                })
            elif "/health" in url or "/readiness" in url or "/broker-capabilities" in url:
                return MockResponse(200, {})
            elif "/tick" in url:
                return MockResponse(200, {})
            elif "/mt5/raw/margin-check" in url or "/mt5/raw/profit-calc" in url:
                return MockResponse(200, {})
            elif "/mt5/raw/market-book" in url:
                return MockResponse(400, text="not_supported")
            return MockResponse(404)
            
        async def post(self, url, **kwargs):
            if "/margin-check" in url or "/profit-calc" in url:
                return MockResponse(200, {})
            if "/order" in url:
                return MockResponse(200, {"order": 12345})
            if "/cancel-order" in url:
                return MockResponse(200, {})
            return MockResponse(404)
            
    return MockAsyncClient

@pytest.mark.asyncio
async def test_conformance_harness(mock_httpx_client, tmp_path):
    with patch('httpx.AsyncClient', new=mock_httpx_client):
        runner = ConformanceRunner(base_url="http://localhost:8001", api_key="test", include_write_tests=True)
        report = await runner.run()
        
        # Verify Report model
        assert report.broker_name == "Test Broker"
        assert report.server == "Test Server"
        assert report.terminal_build == "3802"
        assert report.compatibility_profile == "balanced"
        
        # Check some results
        assert len(report.results) > 0
        market_book_res = next(r for r in report.results if r.name == "market_book")
        assert market_book_res.status == "warn"  # since we mocked 400 not_supported
        
        assert report.recommendation == "balanced" # due to warning

        reporter = ConformanceReporter(report)
        json_out = tmp_path / "report.json"
        md_out = tmp_path / "report.md"
        
        reporter.write_json(str(json_out))
        reporter.write_markdown(str(md_out))
        
        # Verify JSON output
        assert os.path.exists(json_out)
        with open(json_out, "r") as f:
            data = json.load(f)
            assert data["broker_name"] == "Test Broker"
            assert len(data["results"]) == len(report.results)
            
        # Verify Markdown output
        assert os.path.exists(md_out)
        with open(md_out, "r") as f:
            md_content = f.read()
            assert "# Conformance Report" in md_content
            assert "Test Broker" in md_content
            assert "Test Server" in md_content
            assert "## Summary by Category" in md_content
            assert "## Details" in md_content
            assert "## Recommendation" in md_content
