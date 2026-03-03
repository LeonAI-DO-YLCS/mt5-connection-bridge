"""Unit tests — ErrorCode taxonomy enum."""

from app.messaging.codes import ErrorCode


class TestErrorCodeMembers:
    """Verify all 19 enum members have required metadata."""

    REQUIRED_DOMAINS = {"VALIDATION", "MT5", "EXECUTION", "WORKER", "SYMBOL", "REQUEST", "INTERNAL"}
    VALID_SEVERITIES = {"low", "medium", "high", "critical"}
    VALID_CATEGORIES = {"error", "warning", "status", "advice", "success", "info"}

    def test_exactly_19_members(self):
        assert len(ErrorCode) == 19

    def test_no_duplicate_names(self):
        names = [c.name for c in ErrorCode]
        assert len(names) == len(set(names))

    def test_all_members_have_required_metadata(self):
        for code in ErrorCode:
            meta = code.value
            assert meta.domain, f"{code.name} missing domain"
            assert meta.default_title, f"{code.name} missing default_title"
            assert meta.default_message, f"{code.name} missing default_message"
            assert meta.default_action, f"{code.name} missing default_action"
            assert meta.default_severity, f"{code.name} missing default_severity"
            assert isinstance(meta.default_retryable, bool), f"{code.name} retryable must be bool"
            assert isinstance(meta.default_http_status, int), f"{code.name} http_status must be int"
            assert meta.category, f"{code.name} missing category"

    def test_all_domains_in_allowed_set(self):
        for code in ErrorCode:
            assert code.domain in self.REQUIRED_DOMAINS, (
                f"{code.name} has invalid domain '{code.domain}'"
            )

    def test_all_severities_valid(self):
        for code in ErrorCode:
            assert code.default_severity in self.VALID_SEVERITIES, (
                f"{code.name} has invalid severity '{code.default_severity}'"
            )

    def test_all_categories_valid(self):
        for code in ErrorCode:
            assert code.default_category in self.VALID_CATEGORIES, (
                f"{code.name} has invalid category '{code.default_category}'"
            )

    def test_http_statuses_in_range(self):
        for code in ErrorCode:
            assert 200 <= code.default_http_status <= 599, (
                f"{code.name} has invalid http_status {code.default_http_status}"
            )

    def test_convenience_accessors(self):
        code = ErrorCode.VALIDATION_ERROR
        assert code.domain == "VALIDATION"
        assert code.default_title == "Input validation failed"
        assert code.default_severity == "medium"
        assert code.default_retryable is False
        assert code.default_http_status == 422
        assert code.default_category == "error"

    def test_success_code_exists(self):
        ok = ErrorCode.REQUEST_OK
        assert ok.default_category == "success"
        assert ok.default_http_status == 200

    def test_existing_infer_codes_covered(self):
        """All 10 codes from the legacy _infer_error_code() must exist."""
        expected = {
            "UNAUTHORIZED_API_KEY",
            "EXECUTION_DISABLED",
            "SYMBOL_NOT_CONFIGURED",
            "RESOURCE_NOT_FOUND",
            "OVERLOAD_OR_SINGLE_FLIGHT",
            "VALIDATION_ERROR",
            "MT5_DISCONNECTED",
            "SERVICE_UNAVAILABLE",
            "INTERNAL_SERVER_ERROR",
            "REQUEST_ERROR",
        }
        actual = {c.name for c in ErrorCode}
        assert expected.issubset(actual), f"Missing codes: {expected - actual}"
