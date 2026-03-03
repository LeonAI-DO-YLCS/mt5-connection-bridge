"""Unit tests for app.execution.lifecycle (T007)."""

import pytest

from app.execution.lifecycle import (
    OperationContext,
    OperationState,
    create_context,
    transition,
)


class TestOperationState:
    def test_all_states_exist(self):
        expected = {"queued", "dispatching", "accepted", "rejected", "recovered", "failed_terminal"}
        actual = {s.value for s in OperationState}
        assert actual == expected

    def test_str_enum_values(self):
        assert str(OperationState.QUEUED) == "queued"
        assert OperationState.DISPATCHING == "dispatching"


class TestCreateContext:
    def test_defaults(self):
        ctx = create_context("test_op")
        assert ctx.operation == "test_op"
        assert ctx.current_state == OperationState.QUEUED
        assert ctx.state_transitions == [OperationState.QUEUED]
        assert ctx.tracking_id.startswith("brg-")
        assert ctx.idempotency_key is None
        assert ctx.retry_count == 0

    def test_with_idempotency(self):
        ctx = create_context("test_op", idempotency_key="abc-123", request_hash="deadbeef")
        assert ctx.idempotency_key == "abc-123"
        assert ctx.request_hash == "deadbeef"


class TestTransition:
    def test_queued_to_dispatching(self):
        ctx = create_context("test_op")
        transition(ctx, OperationState.DISPATCHING)
        assert ctx.current_state == OperationState.DISPATCHING
        assert ctx.state_transitions == [OperationState.QUEUED, OperationState.DISPATCHING]

    def test_dispatching_to_accepted(self):
        ctx = create_context("test_op")
        transition(ctx, OperationState.DISPATCHING)
        transition(ctx, OperationState.ACCEPTED)
        assert ctx.current_state == OperationState.ACCEPTED

    def test_dispatching_to_rejected(self):
        ctx = create_context("test_op")
        transition(ctx, OperationState.DISPATCHING)
        transition(ctx, OperationState.REJECTED)
        assert ctx.current_state == OperationState.REJECTED

    def test_dispatching_to_failed_terminal(self):
        ctx = create_context("test_op")
        transition(ctx, OperationState.DISPATCHING)
        transition(ctx, OperationState.FAILED_TERMINAL)
        assert ctx.current_state == OperationState.FAILED_TERMINAL

    def test_cannot_transition_from_terminal_accepted(self):
        ctx = create_context("test_op")
        transition(ctx, OperationState.ACCEPTED)
        with pytest.raises(ValueError, match="terminal state"):
            transition(ctx, OperationState.DISPATCHING)

    def test_cannot_transition_from_terminal_rejected(self):
        ctx = create_context("test_op")
        transition(ctx, OperationState.REJECTED)
        with pytest.raises(ValueError, match="terminal state"):
            transition(ctx, OperationState.ACCEPTED)

    def test_cannot_transition_from_terminal_failed(self):
        ctx = create_context("test_op")
        transition(ctx, OperationState.FAILED_TERMINAL)
        with pytest.raises(ValueError, match="terminal state"):
            transition(ctx, OperationState.QUEUED)

    def test_full_lifecycle_happy_path(self):
        ctx = create_context("execute_trade")
        transition(ctx, OperationState.DISPATCHING)
        transition(ctx, OperationState.ACCEPTED)
        assert ctx.state_transitions == [
            OperationState.QUEUED,
            OperationState.DISPATCHING,
            OperationState.ACCEPTED,
        ]
