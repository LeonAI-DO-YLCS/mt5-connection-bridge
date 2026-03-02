from __future__ import annotations

from fastapi import APIRouter

from ..main import metrics_store
from ..models.metrics import MetricsSummary

router = APIRouter(tags=["metrics"])


@router.get("/metrics", response_model=MetricsSummary)
async def metrics_summary() -> MetricsSummary:
    return metrics_store.get_summary()
