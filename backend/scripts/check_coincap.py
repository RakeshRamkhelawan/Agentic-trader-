import asyncio

import httpx


async def check_coincap():
    url = "https://api.coincap.io/v2/assets?limit=50"
    print(f"Fetching from {url}...")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                assets = data["data"]
                print(f"✅ Success! Fetched {len(assets)} assets.")
                print("Top 3:")
                for a in assets[:3]:
                    print(f"- {a['symbol']} ({a['name']}): ${a['priceUsd']}")
            else:
                print(f"❌ Failed: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")


if __name__ == "__main__":
    asyncio.run(check_coincap())
