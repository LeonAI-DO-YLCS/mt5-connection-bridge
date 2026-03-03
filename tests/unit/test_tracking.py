"""Unit tests — Tracking ID generation."""

import re

from app.messaging.tracking import generate_tracking_id

TRACKING_ID_PATTERN = re.compile(r"^brg-\d{8}T\d{6}-[0-9a-f]{4}$")


class TestGenerateTrackingId:
    """Verify format, length, and uniqueness of tracking IDs."""

    def test_format_matches_spec(self):
        tid = generate_tracking_id()
        assert TRACKING_ID_PATTERN.match(tid), f"Bad format: {tid}"

    def test_length_at_most_30(self):
        for _ in range(50):
            tid = generate_tracking_id()
            assert len(tid) <= 30, f"Too long ({len(tid)}): {tid}"

    def test_prefix_is_brg(self):
        tid = generate_tracking_id()
        assert tid.startswith("brg-")

    def test_uniqueness_within_batch(self):
        ids = [generate_tracking_id() for _ in range(100)]
        assert len(set(ids)) == 100, "Duplicate tracking IDs detected"
