"""Test Ollama connection and pull a model if needed."""
import asyncio
import aiohttp
import json


async def test_ollama():
    print("=" * 50)
    print("OLLAMA STATUS CHECK")
    print("=" * 50)
    
    # Test 1: Basic connectivity
    print("\n[1] Checking Ollama server...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:11434/api/tags", timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = data.get("models", [])
                    print(f"   [OK] Ollama is running")
                    print(f"   Models installed: {len(models)}")
                    for m in models:
                        print(f"   - {m.get('name', 'unknown')}")
                else:
                    print(f"   [FAIL] Status: {resp.status}")
                    return
    except Exception as e:
        print(f"   [FAIL] {e}")
        print("   Is Ollama installed? Run: ollama serve")
        return
    
    # Test 2: Pull a model if none installed
    if not models:
        print("\n[2] No models found. Pulling llama3.2 (lightweight)...")
        print("   (This will take a few minutes)")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:11434/api/pull",
                    json={"name": "llama3.2"},
                    timeout=300
                ) as resp:
                    if resp.status == 200:
                        print("   [OK] Model pulled successfully!")
                    else:
                        print(f"   [FAIL] Status: {resp.status}")
        except Exception as e:
            print(f"   [FAIL] {e}")
    
    # Test 3: Generate a test response
    print("\n[3] Testing generation...")
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "llama3.2" if not models else models[0].get("name"),
                "prompt": "What is 2+2? Answer with just the number.",
                "stream": False
            }
            async with session.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=30
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    response = data.get("response", "")
                    print(f"   [OK] Response: {response[:100]}")
                else:
                    print(f"   [FAIL] Status: {resp.status}")
    except Exception as e:
        print(f"   [FAIL] {e}")
    
    print("\n" + "=" * 50)
    print("Test complete!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_ollama())
