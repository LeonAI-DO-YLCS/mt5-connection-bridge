"""Unit tests for retry classification (T010).

Validates that ErrorCode.default_retryable is set correctly for all codes.
"""

from app.messaging.codes import ErrorCode


class TestRetryClassification:
    """Verify retry classification is correct for all error codes."""

    RETRYABLE_CODES = {
        "MT5_DISCONNECTED",
        "MT5_RUNTIME_UNAVAILABLE",
        "SERVICE_UNAVAILABLE",
        "INTERNAL_SERVER_ERROR",
        "OVERLOAD_OR_SINGLE_FLIGHT",
        "READINESS_EVALUATION_FAILED",
    }

    NON_RETRYABLE_CODES = {
        "REQUEST_OK",
        "VALIDATION_VOLUME_RANGE",
        "VALIDATION_VOLUME_STEP",
        "VALIDATION_CURRENT_PRICE_GT_ZERO",
        "VALIDATION_ERROR",
        "EXECUTION_DISABLED",
        "SYMBOL_TRADE_MODE_RESTRICTED",
        "SYMBOL_NOT_CONFIGURED",
        "FILLING_MODE_UNSUPPORTED",
        "REQUEST_REJECTED",
        "RESOURCE_NOT_FOUND",
        "REQUEST_ERROR",
        "UNAUTHORIZED_API_KEY",
        "WORKER_RECONNECT_EXHAUSTED",
        "IDEMPOTENCY_KEY_CONFLICT",
        "IDEMPOTENCY_KEY_REPLAYED",
    }

    def test_retryable_codes_are_retryable(self):
        for name in self.RETRYABLE_CODES:
            code = ErrorCode[name]
            assert code.default_retryable is True, f"{name} should be retryable"

    def test_non_retryable_codes_are_not_retryable(self):
        for name in self.NON_RETRYABLE_CODES:
            code = ErrorCode[name]
            assert code.default_retryable is False, f"{name} should NOT be retryable"

    def test_all_codes_classified(self):
        """Every ErrorCode must be in either RETRYABLE_CODES or NON_RETRYABLE_CODES."""
        all_names = {c.name for c in ErrorCode}
        classified = self.RETRYABLE_CODES | self.NON_RETRYABLE_CODES
        assert all_names == classified, f"Unclassified codes: {all_names - classified}"
