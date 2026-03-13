import httpx
from typing import List
from app.models.conformance import ConformanceResult

async def run_write_tests_probe(client: httpx.AsyncClient) -> List[ConformanceResult]:
    results = []
    
    # 1. Order send and cancel
    try:
        # We try to send a buy limit order very far from current price, then immediately cancel
        # The goal is to verify that we can execute orders
        send_resp = await client.post("/order", json={
            "symbol": "EURUSD",
            "action": "buy",
            "order_type": "limit",
            "volume": 0.01,
            "price": 0.5000, # Very far away
            "magic": 12345
        })
        
        if send_resp.status_code == 200:
            order_data = send_resp.json()
            order_id = order_data.get("order")
            if order_id:
                # Cancel immediately
                cancel_resp = await client.post("/cancel-order", json={"order": order_id})
                if cancel_resp.status_code == 200:
                    results.append(ConformanceResult(category="write_tests", name="order_send_cancel", status="pass"))
                else:
                    results.append(ConformanceResult(category="write_tests", name="order_send_cancel", status="warn", message=f"Order sent but cancel failed: {cancel_resp.status_code}"))
            else:
                results.append(ConformanceResult(category="write_tests", name="order_send_cancel", status="warn", message="Order sent but no ID returned"))
        else:
            results.append(ConformanceResult(category="write_tests", name="order_send_cancel", status="fail", message=f"Send failed: {send_resp.status_code}"))
    except Exception as e:
        results.append(ConformanceResult(category="write_tests", name="order_send_cancel", status="fail", message=str(e)))

    return results
