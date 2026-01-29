import requests
import json

# トップページを確認
try:
    response = requests.get('http://localhost:8001/', timeout=5)
    print(f"トップページ: {response.status_code}")
    if response.status_code == 200:
        print("✓ トップページは正常です")
        # 詳細ページリンクを探す
        if 'article/189' in response.text or 'article/' in response.text:
            print("✓ 詳細ページへのリンクが存在します")
except Exception as e:
    print(f"✗ トップページエラー: {e}")

# 詳細ページをテスト
try:
    response = requests.get('http://localhost:8001/article/189', timeout=5)
    print(f"\n詳細ページ (ID=189): {response.status_code}")
    if response.status_code == 200:
        print("✓ 詳細ページは正常に表示されます")
        # ページ内容を確認
        if 'メンヘラリウム' in response.text:
            print("✓ 記事タイトルが表示されています")
        if 'detail-image-container' in response.text:
            print("✓ 画像コンテナが存在します")
        if '日本年' not in response.text and '202' in response.text:
            print("✓ 日付フォーマットが正常です")
    else:
        print(f"✗ 詳細ページエラー: {response.status_code}")
        print(response.text[:500])
except Exception as e:
    print(f"✗ 詳細ページ接続エラー: {e}")

# ページング (2ページ目)をテスト
try:
    response = requests.get('http://localhost:8001/?page=2', timeout=5)
    print(f"\nページング (?page=2): {response.status_code}")
    if response.status_code == 200:
        print("✓ ページング機能は正常です")
    else:
        print(f"✗ ページングエラー: {response.status_code}")
except Exception as e:
    print(f"✗ ページング接続エラー: {e}")
