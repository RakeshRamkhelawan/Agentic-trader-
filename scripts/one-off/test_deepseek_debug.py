"""Debug DeepSeek API connection."""
import os
import requests
import json
from dotenv import load_dotenv
load_dotenv('.env')

print("=" * 60)
print("DeepSeek API Debug Test")
print("=" * 60)

api_key = os.getenv('DEEPSEEK_API_KEY')
base_url = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')

print(f"Base URL: {base_url}")
print(f"Model: {model}")
print(f"API Key (first 10 chars): {api_key[:10]}..." if api_key else "No API key!")
print("-" * 60)

# Test 1: Without response_format
print("\n[Test 1] Without response_format...")
try:
    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Say 'DeepSeek is working' in 5 words or less."}
        ],
        "temperature": 0.3,
        "max_tokens": 100,
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        text = result["choices"][0]["message"]["content"]
        print(f"[OK] Response: {text}")
    else:
        print(f"[X] Error: {response.text}")

except Exception as e:
    print(f"[X] Exception: {e}")

# Test 2: With response_format
print("\n[Test 2] With response_format (json_object)...")
try:
    payload["response_format"] = {"type": "json_object"}

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        text = result["choices"][0]["message"]["content"]
        print(f"[OK] Response: {text}")
    else:
        print(f"[X] Error: {response.text[:500]}")

except Exception as e:
    print(f"[X] Exception: {e}")

# Test 3: Test with a trading prompt
print("\n[Test 3] Trading analysis prompt...")
try:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a trading analyst. Respond with JSON."},
            {"role": "user", "content": 'Analyze: RSI=65, ADX=28, Price trend is up. Return JSON: {"action": "BUY/SELL/HOLD", "confidence": 0.0-1.0, "reasoning": "brief"}'}
        ],
        "temperature": 0.3,
        "max_tokens": 200,
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        text = result["choices"][0]["message"]["content"]
        print(f"[OK] Response: {text}")

        # Try to parse
        try:
            parsed = json.loads(text)
            print(f"[OK] Parsed action: {parsed.get('action')}")
            print(f"[OK] Confidence: {parsed.get('confidence')}")
        except:
            print("[!] Could not parse as JSON")
    else:
        print(f"[X] Error: {response.text[:500]}")

except Exception as e:
    print(f"[X] Exception: {e}")

print("\n" + "=" * 60)
