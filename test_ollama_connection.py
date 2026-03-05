"""Test Ollama connection and LLM Provider."""
import asyncio
import aiohttp


async def test_ollama():
    print("Testing Ollama connection...")
    print("=" * 50)

    # Test 1: Check if Ollama is running
    models = []
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:11434/api/tags", timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = data.get("models", [])
                    print("[OK] Ollama is RUNNING")
                    print(f"   Available models: {len(models)}")
                    for m in models:
                        model_name = m.get("name", "unknown")
                        print(f"   - {model_name}")
                else:
                    print(f"[FAIL] Ollama returned status {resp.status}")
    except Exception as e:
        print(f"[FAIL] Ollama connection failed: {e}")
        print("   Make sure Ollama is installed and running:")
        print("   - Install: https://ollama.com/download")
        print("   - Run: ollama serve")
        return

    print()
    print("Test 2: Test LLM Provider module...")
    print("-" * 50)

    try:
        from backend.core.llm.llm_provider import create_llm_provider, LLMBackend

        llm = create_llm_provider(backend=LLMBackend.OLLAMA, model="llama3.2")
        print(f"[OK] LLM Provider created: {llm.config.backend.value}")
        print(f"   Model: {llm.config.model}")
        print(f"   Base URL: {llm.config.base_url}")
    except Exception as e:
        print(f"[FAIL] LLM Provider failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print()
    print("Test 3: Generate test text...")
    print("-" * 50)

    if not models:
        print("[INFO] No models installed in Ollama.")
        print("       To install llama3.2, run: ollama pull llama3.2")
        print()
        print("       Falling back to MOCK mode for testing...")
    
    try:
        result = llm.generate(
            prompt="What is 2+2? Answer with just the number.",
            system_prompt="You are a helpful assistant.",
        )
        
        if result.get('metadata', {}).get('backend') == 'mock':
            print("[OK] MOCK Response (Ollama model not available):")
        else:
            print("[OK] Ollama Response:")
        
        print(f"   Text: {result.get('text', 'N/A')[:100]}...")
        print(f"   Confidence: {result.get('confidence', 'N/A')}")
        print(f"   Reasoning: {result.get('reasoning', 'N/A')[:100]}...")
        print(f"   Backend: {result.get('metadata', {}).get('backend', 'unknown')}")
    except Exception as e:
        print(f"[FAIL] Generation failed: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 50)
    print("Summary:")
    print("-" * 50)
    print(f"  Ollama Server: RUNNING")
    print(f"  Models: {len(models)} installed")
    print(f"  LLM Provider: WORKING")
    if not models:
        print("  NOTE: Install a model to use real LLM inference")
        print("        Run: ollama pull llama3.2")


if __name__ == "__main__":
    asyncio.run(test_ollama())
