from typing import Any, Dict, List
from pydantic import BaseModel

class FinancialMetricsResponse(BaseModel):
    financial_metrics: list[dict[str, Any]]

class LineItemResponse(BaseModel):
    search_results: list[dict[str, Any]]

class InsiderTradeResponse(BaseModel):
    insider_trades: list[dict[str, Any]]

class CompanyNewsResponse(BaseModel):
    news: list[dict[str, Any]]

class CompanyFactsResponse(BaseModel):
    company_facts: dict[str, Any]
