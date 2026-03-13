import httpx
from typing import List
from app.models.conformance import ConformanceResult

async def run_calculations_probe(client: httpx.AsyncClient) -> List[ConformanceResult]:
    results = []
    
    # 1. /margin-check (safe domain)
    try:
        resp = await client.post("/margin-check", json={"symbol": "EURUSD", "volume": 1.0, "action": "buy"})
        if resp.status_code == 200:
            results.append(ConformanceResult(category="calculations", name="margin_check_safe", status="pass"))
        else:
            results.append(ConformanceResult(category="calculations", name="margin_check_safe", status="warn", message=f"Status code {resp.status_code}"))
    except Exception as e:
        results.append(ConformanceResult(category="calculations", name="margin_check_safe", status="fail", message=str(e)))
        
    # 2. /profit-calc (safe domain)
    try:
        resp = await client.post("/profit-calc", json={"symbol": "EURUSD", "volume": 1.0, "action": "buy", "price_open": 1.1000, "price_close": 1.1050})
        if resp.status_code == 200:
            results.append(ConformanceResult(category="calculations", name="profit_calc_safe", status="pass"))
        else:
            results.append(ConformanceResult(category="calculations", name="profit_calc_safe", status="warn", message=f"Status code {resp.status_code}"))
    except Exception as e:
        results.append(ConformanceResult(category="calculations", name="profit_calc_safe", status="fail", message=str(e)))
        
    # 3. /mt5/raw/margin-check
    try:
        resp = await client.get("/mt5/raw/margin-check?symbol=EURUSD&volume=1.0&action=buy")
        if resp.status_code == 200:
            results.append(ConformanceResult(category="calculations", name="margin_check_raw", status="pass"))
        else:
            results.append(ConformanceResult(category="calculations", name="margin_check_raw", status="warn", message=f"Status code {resp.status_code}"))
    except Exception as e:
        results.append(ConformanceResult(category="calculations", name="margin_check_raw", status="fail", message=str(e)))

    # 4. /mt5/raw/profit-calc
    try:
        resp = await client.get("/mt5/raw/profit-calc?symbol=EURUSD&volume=1.0&action=buy&price_open=1.1000&price_close=1.1050")
        if resp.status_code == 200:
            results.append(ConformanceResult(category="calculations", name="profit_calc_raw", status="pass"))
        else:
            results.append(ConformanceResult(category="calculations", name="profit_calc_raw", status="warn", message=f"Status code {resp.status_code}"))
    except Exception as e:
        results.append(ConformanceResult(category="calculations", name="profit_calc_raw", status="fail", message=str(e)))

    return results
