"""
Integration tests for close-position comment fallback behavior.

Acceptance Scenarios (from spec.md §Acceptance Scenarios):
* test_close_position_normal_success_no_fallback -> Scenario 2 (normal scenario without comment failure)
* test_close_position_comment_rejected_then_recovered -> Scenario 1 (broker rejects comment, fallback succeeds)
* test_close_position_comment_rejected_then_unrecoverable -> Scenario 3 (broker rejects comment, fallback fails)
* test_close_position_non_comment_failure_no_fallback -> Scenario edge case (unrelated non-comment failure)
"""

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.main import app, settings
from app.mt5_worker import WorkerState


def _setup_mock_mt5():
    mock_mt5 = MagicMock()
    mock_mt5.TRADE_RETCODE_DONE = 10009
    return mock_mt5


@pytest.fixture(autouse=True)
def _setup_env(client, monkeypatch):
    settings.execution_enabled = True
    settings.mt5_bridge_api_key = "test-api-key"
    monkeypatch.setenv("STRICT_HTTP_SEMANTICS", "true")
    with patch("app.routes.close_position.get_state", return_value=WorkerState.AUTHORIZED):
        with patch("app.routes.close_position.submit") as mock_submit:
            from concurrent.futures import Future
            def _submit(fn):
                fut = Future()
                try:
                    fut.set_result(fn())
                except Exception as exc:
                    fut.set_exception(exc)
                return fut
            mock_submit.side_effect = _submit
            yield


def test_close_position_normal_success_no_fallback(client):
    mock_mt5 = _setup_mock_mt5()
    with patch.dict("sys.modules", {"MetaTrader5": mock_mt5}):
        # 1. fake position mapping
        fake_pos = SimpleNamespace(
            ticket=12345,
            symbol="EURUSD",
            type=0,  # OP_BUY
            volume=0.1,
            price_open=1.0800,
            price_current=1.0850,
        )
        mock_mt5.positions_get.return_value = (fake_pos,)
        
        # 2. fake symbol_info
        fake_sym = SimpleNamespace(
            bid=1.0850,
            ask=1.0852,
            point=0.00001,
            trade_exemode=1,
            trade_fillout=1,
            volume_min=0.01,
            volume_step=0.01,
        )
        mock_mt5.symbol_info.return_value = fake_sym
        mock_mt5.symbol_info_tick.return_value = fake_sym
        
        # 3. fake order_send success on FIRST call
        mock_result = SimpleNamespace(
            retcode=10009, price=1.085, volume=0.1, order=9999
        )
        mock_mt5.order_send.return_value = mock_result

        # 4. call the endpoint
        response = client.post(
            "/close-position",
            json={"ticket": 12345},
            headers={"X-API-Key": "test-api-key"}
        )

        # 5. assert success
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True or data.get("ok") is True
        
        # 6. assert exactly ONE call
        assert mock_mt5.order_send.call_count == 1


def test_close_position_comment_rejected_then_recovered(client):
    mock_mt5 = _setup_mock_mt5()
    with patch.dict("sys.modules", {"MetaTrader5": mock_mt5}), \
         patch("app.routes.close_position.emit_operation_log") as mock_emit_log:
        fake_pos = SimpleNamespace(
            ticket=12345, symbol="EURUSD", type=0, volume=0.1, price_current=1.0850
        )
        mock_mt5.positions_get.return_value = (fake_pos,)
        mock_mt5.symbol_info.return_value = SimpleNamespace(trade_exemode=1, trade_fillout=1, bid=1.0850, volume_min=0.01, volume_step=0.01)
        mock_mt5.symbol_info_tick.return_value = SimpleNamespace(bid=1.0850, ask=1.0852)

        # 1. order_send returns None on first call, success on second
        mock_result = SimpleNamespace(retcode=10009, price=1.085, volume=0.1, order=9999)
        mock_mt5.order_send.side_effect = [None, mock_result]
        
        # 2. last_error returns invalid comment signature
        mock_mt5.last_error.return_value = (-2, 'Invalid "comment" argument')

        # 3. Call endpoint
        response = client.post(
            "/close-position",
            json={"ticket": 12345},
            headers={"X-API-Key": "test-api-key"}
        )

        # 4. Assert success
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True or data.get("ok") is True
        
        # 5. Assert observability log emitted right code
        found_call = False
        for call in mock_emit_log.call_args_list:
            if call.kwargs.get("code") == "MT5_REQUEST_COMMENT_INVALID_RECOVERED":
                found_call = True
                break
        assert found_call, "Expected MT5_REQUEST_COMMENT_INVALID_RECOVERED to be logged"
        
        # 6. Assert exactly TWO calls
        assert mock_mt5.order_send.call_count == 2
        
        # 7. Assert second call had no "comment"
        second_call_arg = mock_mt5.order_send.call_args_list[1][0][0]
        assert "comment" not in second_call_arg


def test_close_position_comment_rejected_then_unrecoverable(client):
    mock_mt5 = _setup_mock_mt5()
    with patch.dict("sys.modules", {"MetaTrader5": mock_mt5}):
        fake_pos = SimpleNamespace(
            ticket=12345, symbol="EURUSD", type=0, volume=0.1, price_current=1.0850
        )
        mock_mt5.positions_get.return_value = (fake_pos,)
        mock_mt5.symbol_info.return_value = SimpleNamespace(trade_exemode=1, trade_fillout=1, bid=1.0850, volume_min=0.01, volume_step=0.01)
        mock_mt5.symbol_info_tick.return_value = SimpleNamespace(bid=1.0850, ask=1.0852)

        # 1. order_send returns None on BOTH calls
        mock_mt5.order_send.return_value = None
        
        # 2. last_error returns invalid comment on first call, some other error on second
        mock_mt5.last_error.side_effect = [
            (-2, 'Invalid "comment" argument'),
            (-2, 'Some other error')
        ]

        # 3. Call endpoint
        response = client.post(
            "/close-position",
            json={"ticket": 12345},
            headers={"X-API-Key": "test-api-key"}
        )

        # 4. Assert success is False
        assert response.status_code == 400
        data = response.json()
        assert data.get("success") is False or "error" in data or data.get("ok") is False
        
        # 5. Assert code
        assert data.get("code") == "MT5_REQUEST_COMMENT_INVALID" or response.headers.get("x-error-code") == "MT5_REQUEST_COMMENT_INVALID" or (data.get("detail") and data["detail"].get("code") == "MT5_REQUEST_COMMENT_INVALID")
        
        # 6. Assert exactly TWO calls
        assert mock_mt5.order_send.call_count == 2


def test_close_position_non_comment_failure_no_fallback(client):
    mock_mt5 = _setup_mock_mt5()
    with patch.dict("sys.modules", {"MetaTrader5": mock_mt5}):
        fake_pos = SimpleNamespace(
            ticket=12345, symbol="EURUSD", type=0, volume=0.1, price_current=1.0850
        )
        mock_mt5.positions_get.return_value = (fake_pos,)
        mock_mt5.symbol_info.return_value = SimpleNamespace(trade_exemode=1, trade_fillout=1, bid=1.0850, volume_min=0.01, volume_step=0.01)
        mock_mt5.symbol_info_tick.return_value = SimpleNamespace(bid=1.0850, ask=1.0852)

        # 1. order_send returns None
        mock_mt5.order_send.return_value = None
        
        # 2. last_error returns non-comment related error
        mock_mt5.last_error.return_value = (-2, 'Invalid "volume" argument')

        # 3. Call endpoint
        response = client.post(
            "/close-position",
            json={"ticket": 12345},
            headers={"X-API-Key": "test-api-key"}
        )

        data = response.json()
        
        # 4. Assert ZERO fallback triggered (one attempt only)
        assert mock_mt5.order_send.call_count == 1
        
        # 5. Assert response code mapping (should be standard error mapping, not comment related)
        code = data.get("code") or response.headers.get("x-error-code") or (data.get("detail") and data["detail"].get("code"))
        assert code not in ("MT5_REQUEST_COMMENT_INVALID_RECOVERED", "MT5_REQUEST_COMMENT_INVALID")
