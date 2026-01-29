import requests

for url in ['http://localhost:8001/', 'http://localhost:8001/article/189', 'http://localhost:8001/?page=2']:
    try:
        r = requests.get(url, timeout=10)
        print(url, '->', r.status_code)
        print(r.text[:200])
    except Exception as e:
        print(url, '-> ERROR', e)
