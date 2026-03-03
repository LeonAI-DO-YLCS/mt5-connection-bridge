"""Single-flight guard for trade-affecting operations.

Prevents concurrent duplicate submissions of the same operation type.
Extracted from duplicated per-route implementations.
"""

from __future__ import annotations

import threading

from ..mt5_worker import get_queue_depth


class SingleFlightGuard:
    """Thread-safe single-flight concurrency guard.

    Each trade-affecting route creates its own instance to maintain
    per-route isolation.

    Usage::
        guard = SingleFlightGuard(threshold=100)

        error = guard.acquire()
        if error:
            raise ...  # blocked

        try:
            # ... execute operation ...
        finally:
            guard.release()
    """

    def __init__(self, threshold: int = 100) -> None:
        self._lock = threading.Lock()
        self._inflight: int = 0
        self._threshold = threshold

    def acquire(self) -> str | None:
        """Attempt to acquire the single-flight slot.

        Returns None on success, or an error message string if blocked.
        """
        with self._lock:
            if self._inflight > 0:
                return "Single-flight mode active: wait for current submission to finish."
            pending = self._inflight + get_queue_depth()
            if pending >= self._threshold:
                return (
                    "Execution queue overload protection triggered. "
                    f"Pending={pending}, threshold={self._threshold}."
                )
            self._inflight += 1
        return None

    def release(self) -> None:
        """Release the single-flight slot."""
        with self._lock:
            self._inflight = max(self._inflight - 1, 0)
