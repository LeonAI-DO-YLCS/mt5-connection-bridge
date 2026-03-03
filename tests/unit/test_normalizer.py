"""Unit tests — normalize_error() and normalize_success() factories."""

import re

from app.messaging.codes import ErrorCode
from app.messaging.normalizer import normalize_error, normalize_success

TID = re.compile(r"^brg-\d{8}T\d{6}-[0-9a-f]{4}$")


class TestNormalizeError:
    """Verify error envelope construction."""

    def test_defaults_from_code(self):
        env = normalize_error(ErrorCode.VALIDATION_ERROR)
        assert env.ok is False
        assert env.code == "VALIDATION_ERROR"
        assert env.category == "error"
        assert env.severity == "medium"
        assert env.retryable is False
        assert env.title == "Input validation failed"
        assert TID.match(env.tracking_id)

    def test_custom_message_overrides_default(self):
        env = normalize_error(ErrorCode.MT5_DISCONNECTED, message="Custom disconnect msg")
        assert env.message == "Custom disconnect msg"
        assert env.title == "MT5 terminal disconnected"  # title stays default

    def test_custom_action_overrides_default(self):
        env = normalize_error(ErrorCode.MT5_DISCONNECTED, action="Restart the terminal now")
        assert env.action == "Restart the terminal now"

    def test_context_is_sanitized(self):
        env = normalize_error(
            ErrorCode.VALIDATION_ERROR,
            context={"symbol": "EURUSD", "password": "s3cret"},
        )
        assert "password" not in env.context
        assert env.context == {"symbol": "EURUSD"}

    def test_detail_carried_through(self):
        env = normalize_error(ErrorCode.REQUEST_ERROR, detail="legacy string")
        assert env.detail == "legacy string"

    def test_detail_defaults_to_message(self):
        env = normalize_error(ErrorCode.REQUEST_ERROR, message="bad request")
        assert env.detail == "bad request"

    def test_all_required_fields_present(self):
        env = normalize_error(ErrorCode.INTERNAL_SERVER_ERROR)
        d = env.model_dump()
        for key in ("ok", "category", "code", "tracking_id", "title", "message",
                     "action", "severity", "retryable", "context", "detail"):
            assert key in d, f"Missing field: {key}"


class TestNormalizeSuccess:
    """Verify success envelope construction."""

    def test_defaults(self):
        env = normalize_success()
        assert env.ok is True
        assert env.category == "success"
        assert env.code == "REQUEST_OK"
        assert env.severity == "low"
        assert env.retryable is False
        assert TID.match(env.tracking_id)

    def test_custom_fields(self):
        env = normalize_success(
            title="Trade executed",
            message="Filled 0.01 at 1.085",
            data={"ticket_id": 12345, "filled_price": 1.085},
        )
        assert env.title == "Trade executed"
        assert env.message == "Filled 0.01 at 1.085"
        assert env.data == {"ticket_id": 12345, "filled_price": 1.085}

    def test_data_is_none_by_default(self):
        env = normalize_success()
        assert env.data is None

    def test_all_required_fields_present(self):
        env = normalize_success()
        d = env.model_dump()
        for key in ("ok", "category", "code", "tracking_id", "title", "message",
                     "action", "severity", "retryable", "context"):
            assert key in d, f"Missing field: {key}"
