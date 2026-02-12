import asyncio
import httpx

async def verify_aggregated_markets():
    # Note: We need a valid token or we use a dev path if available
    # For now, let's just check the log output or try to hit the local server if running
    url = "http://127.0.0.1:8000/api/v1/trading/markets"
    
    # We might need to mock the tenant_id dependency if we run this as a script
    # but a better way is to look at the logs of the running Uvicorn process.
    print(f"Checking {url}...")
    try:
        # This will likely fail without auth, but we can check if the server is up
        async with httpx.AsyncClient() as client:
            # Try to get public markets if any
            response = await client.get(url)
            print(f"Status: {response.status_code}")
            data = response.json()
            if isinstance(data, list):
                print(f"Total symbols returned: {len(data)}")
                revolut_count = sum(1 for m in data if "-" in m['symbol'] and len(m['symbol']) > 7) # Simple heuristic
                print(f"Revolut-like symbols: {revolut_count}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_aggregated_markets())
