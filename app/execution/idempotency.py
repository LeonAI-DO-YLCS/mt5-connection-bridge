"""In-memory idempotency store for trade-affecting operations.

Prevents duplicate execution when the same Idempotency-Key header is
submitted multiple times within a bridge session (FR-004 through FR-008).

The store is scoped to the current runtime session — a bridge restart
clears all records (FR-007).
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("mt5_bridge.execution.idempotency")

# Maximum length for idempotency keys (arbitrary safe limit)
MAX_KEY_LENGTH = 128


@dataclass
class IdempotencyRecord:
    """A cached operation result keyed by idempotency key."""

    key: str
    request_hash: str
    response: dict[str, Any]
    created_at: float = field(default_factory=time.monotonic)
    operation: str = ""


def compute_request_hash(body: Any) -> str:
    """SHA-256 hash of the JSON-serialized request body.

    Used to detect Idempotency-Key conflicts (FR-006): same key but
    different request parameters.
    """
    raw = json.dumps(body, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


class IdempotencyStore:
    """Thread-safe in-memory idempotency cache with TTL expiration.

    Usage::
        store = IdempotencyStore(ttl_seconds=3600)

        # Before executing:
        cached = store.check(key, request_hash)
        if cached is not None:
            return cached.response  # replay

        if store.check_conflict(key, request_hash):
            raise IDEMPOTENCY_KEY_CONFLICT

        # After executing:
        store.store(key, request_hash, response_dict, operation)
    """

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._records: dict[str, IdempotencyRecord] = {}
        self._lock = threading.Lock()
        self._ttl = ttl_seconds

    def check(self, key: str, request_hash: str) -> IdempotencyRecord | None:
        """Return the cached record if the key exists with the same hash.

        Returns None if the key doesn't exist or if the hash differs
        (use ``check_conflict`` to distinguish those cases).
        """
        self._cleanup()
        with self._lock:
            record = self._records.get(key)
            if record is not None and record.request_hash == request_hash:
                logger.info("Idempotency cache hit for key=%s", key)
                return record
        return None

    def check_conflict(self, key: str, request_hash: str) -> bool:
        """Return True if the key exists but with a DIFFERENT request hash (FR-006)."""
        with self._lock:
            record = self._records.get(key)
            if record is not None and record.request_hash != request_hash:
                logger.warning(
                    "Idempotency key conflict: key=%s, stored_hash=%s, new_hash=%s",
                    key, record.request_hash[:8], request_hash[:8],
                )
                return True
        return False

    def store(
        self,
        key: str,
        request_hash: str,
        response: dict[str, Any],
        operation: str = "",
    ) -> None:
        """Cache an operation result for later replay (FR-005)."""
        with self._lock:
            self._records[key] = IdempotencyRecord(
                key=key,
                request_hash=request_hash,
                response=response,
                operation=operation,
            )
        logger.debug("Stored idempotency record: key=%s, operation=%s", key, operation)

    def clear(self) -> None:
        """Clear all records (used in tests)."""
        with self._lock:
            self._records.clear()

    def _cleanup(self) -> None:
        """Remove expired records based on TTL."""
        now = time.monotonic()
        with self._lock:
            expired = [
                k for k, r in self._records.items()
                if (now - r.created_at) > self._ttl
            ]
            for k in expired:
                del self._records[k]
            if expired:
                logger.debug("Cleaned up %d expired idempotency records", len(expired))


# Module-level singleton — session-scoped (FR-007).
idempotency_store = IdempotencyStore()
