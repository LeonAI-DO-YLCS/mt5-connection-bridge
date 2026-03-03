"""Unit tests for app.execution.idempotency (T009)."""

import time

from app.execution.idempotency import (
    IdempotencyStore,
    compute_request_hash,
)


class TestComputeRequestHash:
    def test_deterministic(self):
        body = {"ticker": "AAPL", "action": "buy", "quantity": 0.1}
        h1 = compute_request_hash(body)
        h2 = compute_request_hash(body)
        assert h1 == h2

    def test_different_bodies_different_hashes(self):
        h1 = compute_request_hash({"ticker": "AAPL"})
        h2 = compute_request_hash({"ticker": "MSFT"})
        assert h1 != h2

    def test_key_order_irrelevant(self):
        h1 = compute_request_hash({"a": 1, "b": 2})
        h2 = compute_request_hash({"b": 2, "a": 1})
        assert h1 == h2


class TestIdempotencyStore:
    def test_check_returns_none_for_unknown_key(self):
        store = IdempotencyStore(ttl_seconds=60)
        result = store.check("unknown", "hash123")
        assert result is None

    def test_store_and_check_hit(self):
        store = IdempotencyStore(ttl_seconds=60)
        store.store("key-1", "hash-a", {"success": True}, "test_op")
        record = store.check("key-1", "hash-a")
        assert record is not None
        assert record.response == {"success": True}
        assert record.operation == "test_op"

    def test_check_conflict_same_hash(self):
        store = IdempotencyStore(ttl_seconds=60)
        store.store("key-1", "hash-a", {"success": True})
        assert store.check_conflict("key-1", "hash-a") is False

    def test_check_conflict_different_hash(self):
        store = IdempotencyStore(ttl_seconds=60)
        store.store("key-1", "hash-a", {"success": True})
        assert store.check_conflict("key-1", "hash-b") is True

    def test_check_conflict_unknown_key(self):
        store = IdempotencyStore(ttl_seconds=60)
        assert store.check_conflict("unknown", "hash") is False

    def test_ttl_expiration(self):
        store = IdempotencyStore(ttl_seconds=0)  # immediate expiry
        store.store("key-1", "hash-a", {"success": True})
        time.sleep(0.01)  # ensure monotonic time advances
        result = store.check("key-1", "hash-a")
        assert result is None

    def test_clear(self):
        store = IdempotencyStore(ttl_seconds=60)
        store.store("key-1", "hash-a", {"success": True})
        store.clear()
        assert store.check("key-1", "hash-a") is None
