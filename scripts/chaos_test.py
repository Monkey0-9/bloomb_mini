import time
import random
import httpx
import structlog

log = structlog.get_logger()

def run_chaos_test(target_url: str):
    """
    Simulates random failures to test system resilience.
    """
    log.info("starting_chaos_test", target=target_url)
    
    endpoints = [
        "/api/globe/aircraft",
        "/api/globe/thermal",
        "/api/signals",
        "/api/market/prices"
    ]
    
    for _ in range(20):
        ep = random.choice(endpoints)
        try:
            # Simulate high latency or random disconnects (if we could control server)
            # Here we just spam requests to see how it handles load
            resp = httpx.get(f"{target_url}{ep}", timeout=5)
            log.info("chaos_request", endpoint=ep, status=resp.status_code)
        except Exception as e:
            log.warning("chaos_failure", endpoint=ep, error=str(e))
        time.sleep(random.uniform(0.1, 0.5))

if __name__ == "__main__":
    run_chaos_test("http://localhost:9009")
