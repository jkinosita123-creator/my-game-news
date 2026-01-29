import requests

try:
    print("GETリクエストをポート9000に送信...")
    r = requests.get('http://localhost:9000/', timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Size: {len(r.text)}")
    print(f"Headers: {dict(r.headers)}")
    if r.status_code != 200:
        print(f"\nResponse Body:\n{r.text}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
