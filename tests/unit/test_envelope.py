"""Unit tests — MessageEnvelope model and context sanitization."""

import pytest
from pydantic import ValidationError

from app.messaging.envelope import MessageEnvelope, _sanitize_context


class TestMessageEnvelopeModel:
    """Verify field constraints, serialization, and defaults."""

    def _valid_kwargs(self, **overrides):
        base = dict(
            ok=False,
            category="error",
            code="VALIDATION_ERROR",
            tracking_id="brg-20260303T094500-a3f7",
            title="Input validation failed",
            message="One or more fields did not pass validation.",
            action="Check the highlighted fields.",
            severity="medium",
            retryable=False,
        )
        base.update(overrides)
        return base

    def test_minimal_valid_envelope(self):
        env = MessageEnvelope(**self._valid_kwargs())
        assert env.ok is False
        assert env.code == "VALIDATION_ERROR"
        assert env.context == {}
        assert env.detail is None

    def test_all_fields_populated(self):
        env = MessageEnvelope(
            **self._valid_kwargs(
                context={"symbol": "EURUSD"},
                detail="legacy detail string",
                data={"filled_price": 1.085},
            )
        )
        assert env.context == {"symbol": "EURUSD"}
        assert env.detail == "legacy detail string"
        assert env.data == {"filled_price": 1.085}

    def test_title_max_80_chars(self):
        long_title = "A" * 81
        with pytest.raises(ValidationError, match="title"):
            MessageEnvelope(**self._valid_kwargs(title=long_title))

    def test_title_exactly_80_chars_ok(self):
        env = MessageEnvelope(**self._valid_kwargs(title="A" * 80))
        assert len(env.title) == 80

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            MessageEnvelope(**self._valid_kwargs(unknown_field="oops"))

    def test_serialization_roundtrip(self):
        env = MessageEnvelope(
            **self._valid_kwargs(context={"a": 1}, detail="d", data={"x": 2})
        )
        d = env.model_dump()
        assert d["ok"] is False
        assert d["code"] == "VALIDATION_ERROR"
        assert d["context"] == {"a": 1}
        assert d["data"] == {"x": 2}
        env2 = MessageEnvelope(**d)
        assert env2 == env

    def test_success_envelope(self):
        env = MessageEnvelope(
            ok=True,
            category="success",
            code="REQUEST_OK",
            tracking_id="brg-20260303T094500-b1c2",
            title="Trade executed",
            message="Fill at 1.085",
            action="No action required.",
            severity="low",
            retryable=False,
            data={"ticket_id": 12345},
        )
        assert env.ok is True
        assert env.category == "success"


class TestContextSanitization:
    """Verify that sensitive keys are stripped from context."""

    def test_strips_password(self):
        assert _sanitize_context({"password": "s3cret", "symbol": "X"}) == {"symbol": "X"}

    def test_strips_secret(self):
        assert _sanitize_context({"SECRET": "val", "a": 1}) == {"a": 1}

    def test_strips_token(self):
        assert _sanitize_context({"Token": "abc"}) == {}

    def test_strips_key(self):
        assert _sanitize_context({"key": "val"}) == {}

    def test_strips_credential(self):
        assert _sanitize_context({"credential": "x"}) == {}

    def test_none_returns_empty(self):
        assert _sanitize_context(None) == {}

    def test_empty_dict_returns_empty(self):
        assert _sanitize_context({}) == {}

    def test_safe_keys_preserved(self):
        ctx = {"symbol": "EURUSD", "retcode": 10030, "volume": 0.01}
        assert _sanitize_context(ctx) == ctx
