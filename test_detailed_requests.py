#!/usr/bin/env python
"""
詳細なリクエストとレスポンスをロギングする
"""
import requests
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

urls = [
    'http://localhost:9000/',
    'http://localhost:9000/article/189',
    'http://localhost:9000/?page=2'
]

for url in urls:
    print(f"\n{'='*70}")
    print(f"リクエスト: {url}")
    print('='*70)
    
    try:
        response = requests.get(url, timeout=15)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"Content-Length: {len(response.text)}")
        
        if response.status_code == 500:
            print(f"\n🔴 500 Error Detected!")
            print(f"Response Body (first 1000 chars):\n{response.text[:1000]}")
        elif response.status_code == 200:
            print(f"✅ 200 OK - Page loaded successfully")
            # Check if page contains expected content
            if url == 'http://localhost:8001/':
                if '<h5 class="card-title' in response.text:
                    print("   ✓ Contains article cards")
                if 'pagination' in response.text:
                    print("   ✓ Contains pagination")
        else:
            print(f"⚠️  Status {response.status_code}")
            print(f"Response: {response.text[:500]}")
    
    except requests.exceptions.Timeout:
        print(f"❌ Request Timeout (15s)")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")

print(f"\n{'='*70}")
print("Test Complete")
print('='*70)
