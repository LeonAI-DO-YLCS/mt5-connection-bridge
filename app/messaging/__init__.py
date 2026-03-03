"""MT5 Bridge — Messaging normalization module.

Provides canonical message envelope, error code taxonomy,
tracking ID generation, and normalization utilities.
"""

from .codes import ErrorCode
from .envelope import MessageEnvelope, MessageEnvelopeException
from .normalizer import normalize_error, normalize_success
from .tracking import generate_tracking_id

__all__ = [
    "ErrorCode",
    "MessageEnvelope",
    "MessageEnvelopeException",
    "generate_tracking_id",
    "normalize_error",
    "normalize_success",
]
