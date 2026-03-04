"""Unit tests for matches_invalid_comment_signature function."""

import pytest

from app.execution.comment import matches_invalid_comment_signature


@pytest.mark.parametrize(
    "error_code, error_message, expected",
    [
        (-2, 'Invalid "comment" argument', True),
        (-2, 'INVALID "COMMENT" ARGUMENT', True),
        (-2, 'Invalid "volume" argument', False),
        (-1, 'Invalid "comment" argument', False),
        (-2, 'Something else', False),
        (-2, '', False),
    ],
)
def test_matches_invalid_comment_signature(error_code, error_message, expected):
    assert matches_invalid_comment_signature(error_code, error_message) is expected
