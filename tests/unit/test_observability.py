"""Unit tests for app.execution.observability (T017)."""

import logging

from app.execution.lifecycle import create_context
from app.execution.observability import emit_operation_log


class TestEmitOperationLog:
    def test_log_contains_required_fields(self, caplog):
        ctx = create_context("test_op", idempotency_key="key-42")
        with caplog.at_level(logging.INFO, logger="mt5_bridge.execution.observability"):
            emit_operation_log(ctx, code="REQUEST_OK", final_outcome="fill_confirmed")

        assert len(caplog.records) == 1
        msg = caplog.records[0].message
        assert "tracking_id" in msg
        assert "test_op" in msg
        assert "REQUEST_OK" in msg
        assert "fill_confirmed" in msg
        assert "key-42" in msg

    def test_log_without_idempotency_key(self, caplog):
        ctx = create_context("test_op")
        with caplog.at_level(logging.INFO, logger="mt5_bridge.execution.observability"):
            emit_operation_log(ctx, code="REQUEST_REJECTED", final_outcome="order_rejected")

        assert len(caplog.records) == 1
        msg = caplog.records[0].message
        assert "REQUEST_REJECTED" in msg
        assert "None" in msg  # idempotency_key is None
