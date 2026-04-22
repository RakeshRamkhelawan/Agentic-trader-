"""Test DeepSeek API connection."""
import os
from dotenv import load_dotenv
load_dotenv('.env')

from backend.core.llm.llm_provider import create_llm_provider, LLMBackend

print("=" * 60)
print("Testing DeepSeek API Connection")
print("=" * 60)
print(f"API Key present: {bool(os.getenv('DEEPSEEK_API_KEY'))}")
print(f"Model: {os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')}")
print(f"Base URL: {os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')}")
print("-" * 60)

try:
    llm = create_llm_provider(backend=LLMBackend.DEEPSEEK, model='deepseek-chat')

    print("Sending test prompt...")
    result = llm.generate('Say "DeepSeek is working" in 5 words or less.', temperature=0.3)

    print("\n[OK] SUCCESS!")
    print(f"Response: {result}")

except Exception as e:
    print(f"\n[X] ERROR: {e}")
    import traceback
    traceback.print_exc()
