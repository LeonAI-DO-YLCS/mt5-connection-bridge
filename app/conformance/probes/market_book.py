import httpx
from typing import List
from app.models.conformance import ConformanceResult

async def run_market_book_probe(client: httpx.AsyncClient) -> List[ConformanceResult]:
    results = []
    
    # 1. /mt5/raw/market-book
    try:
        resp = await client.get("/mt5/raw/market-book?symbol=EURUSD")
        if resp.status_code == 200:
            results.append(ConformanceResult(category="market_book", name="market_book", status="pass"))
        elif resp.status_code == 400 and "not_supported" in resp.text:
            # Handle not_supported gracefully
            results.append(ConformanceResult(category="market_book", name="market_book", status="warn", message="Not supported by broker"))
        else:
            results.append(ConformanceResult(category="market_book", name="market_book", status="fail", message=f"Status code {resp.status_code}"))
    except Exception as e:
        results.append(ConformanceResult(category="market_book", name="market_book", status="fail", message=str(e)))

    return results
