from __future__ import annotations

import statistics
import time


def test_dashboard_interaction_latency_under_3s(client, auth_headers):
    durations = []

    for _ in range(5):
        start = time.perf_counter()
        resp = client.get("/dashboard/", headers=auth_headers)
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        durations.append(elapsed)

    p99_like = max(durations)
    assert p99_like <= 3.0
    assert statistics.mean(durations) <= 3.0
