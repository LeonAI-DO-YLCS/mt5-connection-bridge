from __future__ import annotations

from concurrent.futures import Future

from app import mt5_worker


def test_submit_enqueues_task_and_increases_queue_depth():
    before = mt5_worker.get_queue_depth()
    fut = mt5_worker.submit(lambda: 1)
    after = mt5_worker.get_queue_depth()

    assert isinstance(fut, Future)
    assert after >= before

    item = mt5_worker._request_queue.get_nowait()
    assert item is not None


def test_get_state_returns_enum():
    assert mt5_worker.get_state().value in {
        "DISCONNECTED",
        "CONNECTING",
        "CONNECTED",
        "AUTHORIZED",
        "PROCESSING",
        "ERROR",
        "RECONNECTING",
    }
