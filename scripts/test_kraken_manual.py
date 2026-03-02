
import urllib.parse
import urllib.request
import json
import time
import hashlib
import hmac
import base64
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("KRAKEN_API_KEY")
API_SECRET = os.getenv("KRAKEN_API_SECRET")
TWOFA_PASSWORD = os.getenv("KRAKEN_2FA_PASSWORD")

API_URL = "https://api.kraken.com"
API_VERSION = "0"

def create_signature(api_path, post_data, api_secret):
    post_data_dict = dict(urllib.parse.parse_qsl(post_data))
    nonce = post_data_dict.get('nonce', '')
    message = (nonce + post_data).encode()
    message_hash = hashlib.sha256(message).digest()
    path_hash = hashlib.sha256(api_path.encode() + message_hash).digest()
    secret_decoded = base64.b64decode(api_secret)
    signature = hmac.new(secret_decoded, path_hash, hashlib.sha512)
    return base64.b64encode(signature.digest()).decode()

def make_api_request(endpoint, data=None, api_key=None, api_secret=None):
    is_private = api_key is not None
    api_path = f"/{API_VERSION}/{'private' if is_private else 'public'}/{endpoint}"
    if data is None:
        data = {}
    if is_private:
        data['nonce'] = str(int(time.time() * 1000))
    post_data = urllib.parse.urlencode(data)
    headers = {'User-Agent': 'Kraken Python API Test Script'}
    if is_private:
        headers['API-Key'] = api_key
        headers['API-Sign'] = create_signature(api_path, post_data, api_secret)
    url = API_URL + api_path
    request = urllib.request.Request(url, post_data.encode(), headers)
    try:
        response = urllib.request.urlopen(request, timeout=10)
        return json.loads(response.read().decode())
    except Exception as e:
        return {'error': [str(e)]}

if __name__ == "__main__":
    print(f"Testing Kraken with API Key: {API_KEY[:10]}...")
    
    print("\n1. Testing WITHOUT 2FA...")
    result_no_2fa = make_api_request(
        'Balance',
        data={},
        api_key=API_KEY,
        api_secret=API_SECRET
    )
    if 'error' in result_no_2fa and len(result_no_2fa['error']) > 0:
        print(f"❌ Failed without 2FA: {result_no_2fa['error']}")
    else:
        print("✅ Success WITHOUT 2FA!")
        print(json.dumps(result_no_2fa.get('result', {}), indent=2))

    print("\n2. Testing WITH 2FA...")
    result_with_2fa = make_api_request(
        'Balance',
        data={'otp': TWOFA_PASSWORD},
        api_key=API_KEY,
        api_secret=API_SECRET
    )
    if 'error' in result_with_2fa and len(result_with_2fa['error']) > 0:
        print(f"❌ Failed with 2FA: {result_with_2fa['error']}")
    else:
        print("✅ Success WITH 2FA!")
        print(json.dumps(result_with_2fa.get('result', {}), indent=2))
