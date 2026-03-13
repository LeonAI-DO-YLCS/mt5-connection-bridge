import httpx
from typing import List
from app.models.conformance import ConformanceResult

async def run_connection_probe(client: httpx.AsyncClient) -> List[ConformanceResult]:
    results = []
    
    # 1. /health
    try:
        resp = await client.get("/health")
        if resp.status_code == 200:
            results.append(ConformanceResult(category="connection", name="health_check", status="pass"))
        else:
            results.append(ConformanceResult(category="connection", name="health_check", status="fail", message=f"Status code {resp.status_code}"))
    except Exception as e:
        results.append(ConformanceResult(category="connection", name="health_check", status="fail", message=str(e)))
        
    # 2. /diagnostics/runtime
    try:
        resp = await client.get("/diagnostics/runtime")
        if resp.status_code == 200:
            results.append(ConformanceResult(category="connection", name="diagnostics", status="pass"))
        else:
            results.append(ConformanceResult(category="connection", name="diagnostics", status="fail", message=f"Status code {resp.status_code}"))
    except Exception as e:
        results.append(ConformanceResult(category="connection", name="diagnostics", status="fail", message=str(e)))
        
    # 3. /readiness
    try:
        resp = await client.get("/readiness")
        if resp.status_code == 200:
            results.append(ConformanceResult(category="connection", name="readiness", status="pass"))
        else:
            results.append(ConformanceResult(category="connection", name="readiness", status="warn", message=f"Status code {resp.status_code}"))
    except Exception as e:
        results.append(ConformanceResult(category="connection", name="readiness", status="fail", message=str(e)))

    return results
