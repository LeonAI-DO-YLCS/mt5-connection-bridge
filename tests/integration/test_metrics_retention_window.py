from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.metrics import RollingMetrics


def test_metrics_retention_prunes_older_than_90_days(tmp_path):
    log_path = tmp_path / "metrics.jsonl"
    metrics = RollingMetrics(retention_days=90, log_path=log_path)

    old = datetime.now(timezone.utc) - timedelta(days=120)
    recent = datetime.now(timezone.utc) - timedelta(days=10)

    log_path.write_text(
        "\n".join(
            [
                f'{{"timestamp":"{old.isoformat()}","endpoint":"/health","status_code":200}}',
                f'{{"timestamp":"{recent.isoformat()}","endpoint":"/metrics","status_code":200}}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    metrics._prune_old_entries()

    lines = [line for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 1
    assert "/metrics" in lines[0]
