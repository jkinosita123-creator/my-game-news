import requests
import traceback

print("=" * 60)
print("トップページテスト")
print("=" * 60)

try:
    r = requests.get('http://localhost:8001/', timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Headers: {dict(r.headers)}")
    if r.status_code != 200:
        print(f"\nResponse Body:\n{r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("詳細ページテスト (ID=189)")
print("=" * 60)

try:
    r = requests.get('http://localhost:8001/article/189', timeout=10)
    print(f"Status: {r.status_code}")
    if r.status_code != 200:
        print(f"\nResponse Body:\n{r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("ページング テスト (?page=2)")
print("=" * 60)

try:
    r = requests.get('http://localhost:8001/?page=2', timeout=10)
    print(f"Status: {r.status_code}")
    if r.status_code != 200:
        print(f"\nResponse Body:\n{r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
