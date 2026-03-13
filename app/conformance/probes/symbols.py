import httpx
from typing import List
from app.models.conformance import ConformanceResult

async def run_symbols_probe(client: httpx.AsyncClient) -> List[ConformanceResult]:
    results = []
    
    # 1. /broker-capabilities
    try:
        resp = await client.get("/broker-capabilities")
        if resp.status_code == 200:
            results.append(ConformanceResult(category="symbols", name="broker_capabilities", status="pass"))
        else:
            results.append(ConformanceResult(category="symbols", name="broker_capabilities", status="fail", message=f"Status code {resp.status_code}"))
    except Exception as e:
        results.append(ConformanceResult(category="symbols", name="broker_capabilities", status="fail", message=str(e)))

    return results
