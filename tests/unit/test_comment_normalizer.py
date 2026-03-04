"""Unit tests for CommentNormalizer class."""

import pytest

from app.execution.comment import CommentNormalizer


def test_normalize_none_returns_empty_string():
    assert CommentNormalizer().normalize(None) == ""


def test_normalize_empty_string_returns_empty():
    assert CommentNormalizer().normalize("") == ""


def test_normalize_whitespace_only_returns_empty():
    assert CommentNormalizer().normalize("   ") == ""


@pytest.mark.parametrize(
    "input_val, expected_output",
    [
        ("hello@world", "helloworld"),
        ("test! (value)", "test value"),
        ("αβγ unicode", "unicode"),
        ('quote "test"', "quote test"),
        ("special#$%^&*chars", "specialchars"),
        ("pipe|and<angle>brackets", "pipeandanglebrackets"),
    ],
)
def test_normalize_strips_disallowed_characters(input_val, expected_output):
    assert CommentNormalizer().normalize(input_val) == expected_output


@pytest.mark.parametrize(
    "input_val, expected_output",
    [
        ("a" * 26, "a" * 26),
        ("a" * 27, "a" * 26),
        ("a" * 50, "a" * 26),
    ],
)
def test_normalize_enforces_max_length(input_val, expected_output):
    assert CommentNormalizer().normalize(input_val) == expected_output


def test_normalize_preserves_valid_characters():
    assert CommentNormalizer().normalize("valid.comment-123_ok") == "valid.comment-123_ok"


def test_normalize_strips_trailing_whitespace_after_truncation():
    # 25 characters of 'a', then space as the 26th character
    input_str = "a" * 25 + " zzzz"
    result = CommentNormalizer().normalize(input_str)
    assert len(result) <= CommentNormalizer.MAX_LENGTH
    assert result == "a" * 25
    assert not result.endswith(" ")


def test_normalize_full_pipeline_combined():
    input_str = "  ai-hedge-fund@mt5! bridge close order   "
    result = CommentNormalizer().normalize(input_str)
    assert len(result) <= CommentNormalizer.MAX_LENGTH
    assert result == "ai-hedge-fundmt5 bridge cl"
    assert not result.startswith(" ")
    assert not result.endswith(" ")
