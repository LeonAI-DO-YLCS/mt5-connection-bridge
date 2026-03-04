"""Comment normalization and invalid-comment signature detection for MT5 compatibility.

This module provides utilities to sanitize comment values before they reach
MT5's order_send() function and to detect when a broker/terminal has
rejected a comment field based on a specific error signature.
"""

from __future__ import annotations
import re


class CommentNormalizer:
    """Normalizes comment values to comply with MT5 broker/terminal constraints.
    
    Applies max-length, allowed-character, whitespace-trim, and empty-value
    policies to all comment values before they reach order_send().
    """

    MAX_LENGTH: int = 26
    """Maximum allowed comment length after normalization."""

    ALLOWED_PATTERN: re.Pattern = re.compile(r"[^A-Za-z0-9 ._-]")
    """Compiled regex for allowed characters: [A-Za-z0-9 ._-]."""

    def normalize(self, value: str | None) -> str:
        """Applies full normalization pipeline to a comment value.

        Pipeline:
        1. If value is None, return ""
        2. Remove disallowed characters using ALLOWED_PATTERN
        3. Strip leading/trailing whitespace
        4. Truncate to MAX_LENGTH characters
        5. Strip trailing whitespace again (in case truncation landed mid-word)
        6. Return result

        Args:
            value: The comment value to normalize, or None.

        Returns:
            A normalized string that complies with MT5 constraints.
        """
        if value is None:
            return ""
        value = self.ALLOWED_PATTERN.sub("", value)
        value = value.strip()
        value = value[:self.MAX_LENGTH]
        value = value.rstrip()
        return value


def matches_invalid_comment_signature(error_code: int, error_message: str) -> bool:
    """Checks if an error tuple matches the invalid-comment signature.

    Returns True only for the confirmed pattern:
    - error_code == -2 (MT5 API invalid-argument code)
    - "invalid" appears in error_message.lower()
    - "comment" appears in error_message.lower()

    All three conditions must be true. This is intentionally narrow to
    prevent false positives on other -2 errors like "Invalid volume".

    Args:
        error_code: The error code from mt5.last_error().
        error_message: The error message from mt5.last_error().

    Returns:
        True if and only if the error matches the invalid-comment signature.
    """
    return error_code == -2 and "invalid" in error_message.lower() and "comment" in error_message.lower()
