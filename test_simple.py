import requests

try:
    print("GET / (トップページ)")
    r = requests.get('http://localhost:9000/', timeout=5)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print(f"Size: {len(r.text)} bytes")
        print("✅ Success!")
    else:
        print(f"Error: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
