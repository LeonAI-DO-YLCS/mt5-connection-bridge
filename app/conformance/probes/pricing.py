import httpx
from typing import List
from app.models.conformance import ConformanceResult

async def run_pricing_probe(client: httpx.AsyncClient) -> List[ConformanceResult]:
    results = []
    
    # 1. /tick/{symbol}
    # For testing, we can try EURUSD, a very common symbol.
    symbol = "EURUSD"
    try:
        resp = await client.get(f"/tick/{symbol}")
        if resp.status_code == 200:
            results.append(ConformanceResult(category="pricing", name="tick_data", status="pass"))
        elif resp.status_code == 404:
            results.append(ConformanceResult(category="pricing", name="tick_data", status="warn", message=f"Symbol {symbol} not found"))
        else:
            results.append(ConformanceResult(category="pricing", name="tick_data", status="fail", message=f"Status code {resp.status_code}"))
    except Exception as e:
        results.append(ConformanceResult(category="pricing", name="tick_data", status="fail", message=str(e)))

    return results
