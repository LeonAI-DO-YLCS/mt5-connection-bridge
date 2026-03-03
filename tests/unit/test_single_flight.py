"""Unit tests for app.execution.single_flight (T016)."""

from unittest.mock import patch

from app.execution.single_flight import SingleFlightGuard


class TestSingleFlightGuard:
    @patch("app.execution.single_flight.get_queue_depth", return_value=0)
    def test_acquire_success(self, _mock_depth):
        guard = SingleFlightGuard(threshold=100)
        error = guard.acquire()
        assert error is None
        guard.release()

    @patch("app.execution.single_flight.get_queue_depth", return_value=0)
    def test_acquire_blocked_when_inflight(self, _mock_depth):
        guard = SingleFlightGuard(threshold=100)
        guard.acquire()  # first request
        error = guard.acquire()  # should be blocked
        assert error is not None
        assert "Single-flight" in error
        guard.release()

    @patch("app.execution.single_flight.get_queue_depth", return_value=100)
    def test_acquire_blocked_when_overloaded(self, _mock_depth):
        guard = SingleFlightGuard(threshold=100)
        error = guard.acquire()
        assert error is not None
        assert "overload" in error.lower()

    @patch("app.execution.single_flight.get_queue_depth", return_value=0)
    def test_release_allows_reacquire(self, _mock_depth):
        guard = SingleFlightGuard(threshold=100)
        guard.acquire()
        guard.release()
        error = guard.acquire()
        assert error is None
        guard.release()

    @patch("app.execution.single_flight.get_queue_depth", return_value=0)
    def test_release_clamps_to_zero(self, _mock_depth):
        guard = SingleFlightGuard(threshold=100)
        guard.release()  # should not go negative
        guard.release()  # extra release
        error = guard.acquire()
        assert error is None
        guard.release()
