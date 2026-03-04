import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def _setup_mock_mt5():
    mock_mt5 = MagicMock()
    mock_mt5.TRADE_RETCODE_DONE = 10009
    return mock_mt5

def test_close_position_print():
    mock_mt5 = _setup_mock_mt5()
    with patch.dict("sys.modules", {"MetaTrader5": mock_mt5}):
        fake_pos = SimpleNamespace(
            ticket=12345, symbol="EURUSD", type=0, volume=0.1, price_open=1.0800, price_current=1.0850
        )
        mock_mt5.positions_get.return_value = (fake_pos,)
        fake_sym = SimpleNamespace(
            bid=1.0850, ask=1.0852, point=0.00001, trade_exemode=1, trade_fillout=1, volume_min=0.01, volume_step=0.01
        )
        mock_mt5.symbol_info.return_value = fake_sym
        mock_mt5.symbol_info_tick.return_value = fake_sym
        mock_result = SimpleNamespace(retcode=10009, price=1.085, volume=0.1, order=9999)
        mock_mt5.order_send.return_value = mock_result

        response = client.post("/close-position", json={"ticket": 12345}, headers={"X-API-Key": "test-key-1"})
        print(response.json())
        assert response.status_code == 200

