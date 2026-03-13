import os
import requests
import logging
from fastapi import APIRouter, HTTPException, Query, Body

from ..main import symbol_map
from ..models.fundamentals import (
    FinancialMetricsResponse,
    LineItemResponse,
    InsiderTradeResponse,
    CompanyNewsResponse,
    CompanyFactsResponse
)

logger = logging.getLogger("mt5_bridge.fundamentals")
router = APIRouter(tags=["fundamentals"])

def _is_mt5_native(ticker: str) -> bool:
    if ticker not in symbol_map:
        return False
    cat = str(symbol_map[ticker].category).lower()
    return cat in ("synthetic", "forex", "crypto")

def _get_headers() -> dict:
    key = os.environ.get("FINANCIAL_DATASETS_API_KEY")
    if key:
        return {"X-API-KEY": key}
    return {}

@router.get("/financial-metrics", response_model=FinancialMetricsResponse)
async def get_financial_metrics(
    ticker: str = Query(..., description="User-facing ticker name"),
    end_date: str = Query(..., description="End date"),
    period: str = Query("ttm"),
    limit: int = Query(10),
):
    if _is_mt5_native(ticker):
        return FinancialMetricsResponse(financial_metrics=[])
        
    url = f"https://api.financialdatasets.ai/financial-metrics/?ticker={ticker}&report_period_lte={end_date}&limit={limit}&period={period}"
    try:
        resp = requests.get(url, headers=_get_headers())
        if resp.status_code == 200:
            return resp.json()
    except Exception as exc:
        logger.warning(f"Error fetching proxy metrics for {ticker}: {exc}")
    return FinancialMetricsResponse(financial_metrics=[])

@router.post("/line-items/search", response_model=LineItemResponse)
async def search_line_items(
    body: dict = Body(...)
):
    tickers = body.get("tickers", [])
    if not tickers:
        return LineItemResponse(search_results=[])
    ticker = tickers[0]
    
    if _is_mt5_native(ticker):
        return LineItemResponse(search_results=[])
        
    url = "https://api.financialdatasets.ai/financials/search/line-items"
    try:
        resp = requests.post(url, headers=_get_headers(), json=body)
        if resp.status_code == 200:
            return resp.json()
    except Exception as exc:
        logger.warning(f"Error fetching proxy line items for {ticker}: {exc}")
    return LineItemResponse(search_results=[])

@router.get("/insider-trades", response_model=InsiderTradeResponse)
async def get_insider_trades(
    ticker: str = Query(...),
    end_date: str = Query(...),
    start_date: str | None = Query(None),
    limit: int = Query(1000),
):
    if _is_mt5_native(ticker):
        return InsiderTradeResponse(insider_trades=[])
        
    url = f"https://api.financialdatasets.ai/insider-trades/?ticker={ticker}&filing_date_lte={end_date}&limit={limit}"
    if start_date:
        url += f"&filing_date_gte={start_date}"
        
    try:
        resp = requests.get(url, headers=_get_headers())
        if resp.status_code == 200:
            return resp.json()
    except Exception as exc:
        logger.warning(f"Error fetching proxy insider trades for {ticker}: {exc}")
    return InsiderTradeResponse(insider_trades=[])

@router.get("/company-news", response_model=CompanyNewsResponse)
async def get_company_news(
    ticker: str = Query(...),
    end_date: str = Query(...),
    start_date: str | None = Query(None),
    limit: int = Query(1000),
):
    if _is_mt5_native(ticker):
        return CompanyNewsResponse(news=[])
        
    url = f"https://api.financialdatasets.ai/news/?ticker={ticker}&end_date={end_date}&limit={limit}"
    if start_date:
        url += f"&start_date={start_date}"
        
    try:
        resp = requests.get(url, headers=_get_headers())
        if resp.status_code == 200:
            return resp.json()
    except Exception as exc:
        logger.warning(f"Error fetching proxy company news for {ticker}: {exc}")
    return CompanyNewsResponse(news=[])

@router.get("/company-facts", response_model=CompanyFactsResponse)
async def get_company_facts(
    ticker: str = Query(...),
):
    if _is_mt5_native(ticker):
        return CompanyFactsResponse(company_facts={"ticker": ticker, "name": ticker})
        
    url = f"https://api.financialdatasets.ai/company/facts/?ticker={ticker}"
    try:
        resp = requests.get(url, headers=_get_headers())
        if resp.status_code == 200:
            return resp.json()
    except Exception as exc:
        logger.warning(f"Error fetching proxy company facts for {ticker}: {exc}")
    return CompanyFactsResponse(company_facts={"ticker": ticker, "name": ticker})
