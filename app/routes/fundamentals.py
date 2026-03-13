from __future__ import annotations

import logging
import os
from typing import Any

import requests
from fastapi import APIRouter, Body, Query

from ..main import symbol_map
from ..models.fundamentals import (
    CompanyFactsItem,
    CompanyFactsResponse,
    CompanyNewsItem,
    CompanyNewsResponse,
    FinancialMetricItem,
    FinancialMetricsResponse,
    InsiderTradeItem,
    InsiderTradeResponse,
    LineItemResponse,
    LineItemResult,
)

logger = logging.getLogger("mt5_bridge.fundamentals")
router = APIRouter(tags=["fundamentals"])


def _is_mt5_native(ticker: str) -> bool:
    entry = symbol_map.get(ticker)
    if entry is None:
        return False
    return str(entry.category).lower() in {"synthetic", "forex", "crypto"}


def _get_headers() -> dict[str, str]:
    key = os.environ.get("FINANCIAL_DATASETS_API_KEY", "").strip()
    return {"X-API-KEY": key} if key else {}


def _proxy_get(url: str) -> dict[str, Any]:
    resp = requests.get(url, headers=_get_headers(), timeout=10)
    resp.raise_for_status()
    payload = resp.json()
    return payload if isinstance(payload, dict) else {}


def _proxy_post(url: str, body: dict[str, Any]) -> dict[str, Any]:
    resp = requests.post(url, headers=_get_headers(), json=body, timeout=10)
    resp.raise_for_status()
    payload = resp.json()
    return payload if isinstance(payload, dict) else {}


def _normalize_items(payload: dict[str, Any], key: str, model_cls: type) -> list[Any]:
    raw_items = payload.get(key, [])
    if not isinstance(raw_items, list):
        return []

    normalized: list[Any] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        try:
            normalized.append(model_cls(**item))
        except Exception as exc:
            logger.warning(
                "Discarding invalid %s payload item=%s error=%s", key, item, exc
            )
    return normalized


def _default_company_facts(ticker: str) -> CompanyFactsResponse:
    return CompanyFactsResponse(
        company_facts=CompanyFactsItem(ticker=ticker, name=ticker)
    )


@router.get("/financial-metrics", response_model=FinancialMetricsResponse)
async def get_financial_metrics(
    ticker: str = Query(..., description="User-facing ticker name"),
    end_date: str = Query(..., description="End date"),
    period: str = Query("ttm"),
    limit: int = Query(10),
) -> FinancialMetricsResponse:
    if _is_mt5_native(ticker):
        return FinancialMetricsResponse(financial_metrics=[])

    url = (
        "https://api.financialdatasets.ai/financial-metrics/"
        f"?ticker={ticker}&report_period_lte={end_date}&limit={limit}&period={period}"
    )
    try:
        payload = _proxy_get(url)
    except Exception as exc:
        logger.warning("Error fetching proxy metrics for %s: %s", ticker, exc)
        return FinancialMetricsResponse(financial_metrics=[])

    return FinancialMetricsResponse(
        financial_metrics=_normalize_items(
            payload, "financial_metrics", FinancialMetricItem
        )
    )


@router.post("/line-items/search", response_model=LineItemResponse)
async def search_line_items(body: dict[str, Any] = Body(...)) -> LineItemResponse:
    tickers = body.get("tickers", [])
    if not isinstance(tickers, list) or not tickers:
        return LineItemResponse(search_results=[])
    ticker = str(tickers[0])

    if _is_mt5_native(ticker):
        return LineItemResponse(search_results=[])

    url = "https://api.financialdatasets.ai/financials/search/line-items"
    try:
        payload = _proxy_post(url, body)
    except Exception as exc:
        logger.warning("Error fetching proxy line items for %s: %s", ticker, exc)
        return LineItemResponse(search_results=[])

    return LineItemResponse(
        search_results=_normalize_items(payload, "search_results", LineItemResult)
    )


@router.get("/insider-trades", response_model=InsiderTradeResponse)
async def get_insider_trades(
    ticker: str = Query(...),
    end_date: str = Query(...),
    start_date: str | None = Query(None),
    limit: int = Query(1000),
) -> InsiderTradeResponse:
    if _is_mt5_native(ticker):
        return InsiderTradeResponse(insider_trades=[])

    url = f"https://api.financialdatasets.ai/insider-trades/?ticker={ticker}&filing_date_lte={end_date}&limit={limit}"
    if start_date:
        url += f"&filing_date_gte={start_date}"

    try:
        payload = _proxy_get(url)
    except Exception as exc:
        logger.warning("Error fetching proxy insider trades for %s: %s", ticker, exc)
        return InsiderTradeResponse(insider_trades=[])

    return InsiderTradeResponse(
        insider_trades=_normalize_items(payload, "insider_trades", InsiderTradeItem)
    )


@router.get("/company-news", response_model=CompanyNewsResponse)
async def get_company_news(
    ticker: str = Query(...),
    end_date: str = Query(...),
    start_date: str | None = Query(None),
    limit: int = Query(1000),
) -> CompanyNewsResponse:
    if _is_mt5_native(ticker):
        return CompanyNewsResponse(news=[])

    url = f"https://api.financialdatasets.ai/news/?ticker={ticker}&end_date={end_date}&limit={limit}"
    if start_date:
        url += f"&start_date={start_date}"

    try:
        payload = _proxy_get(url)
    except Exception as exc:
        logger.warning("Error fetching proxy company news for %s: %s", ticker, exc)
        return CompanyNewsResponse(news=[])

    return CompanyNewsResponse(news=_normalize_items(payload, "news", CompanyNewsItem))


@router.get("/company-facts", response_model=CompanyFactsResponse)
async def get_company_facts(ticker: str = Query(...)) -> CompanyFactsResponse:
    if _is_mt5_native(ticker):
        return _default_company_facts(ticker)

    url = f"https://api.financialdatasets.ai/company/facts/?ticker={ticker}"
    try:
        payload = _proxy_get(url)
        facts_payload = payload.get("company_facts")
        if not isinstance(facts_payload, dict):
            return _default_company_facts(ticker)
        return CompanyFactsResponse(company_facts=CompanyFactsItem(**facts_payload))
    except Exception as exc:
        logger.warning("Error fetching proxy company facts for %s: %s", ticker, exc)
        return _default_company_facts(ticker)
