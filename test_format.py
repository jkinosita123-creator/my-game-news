from datetime import datetime

# published_at が datetime の場合のテスト
article = {
    'id': 189,
    'title': 'テスト記事',
    'published_at': datetime(2026, 1, 29, 13, 19, 14),
    'source': 'テスト',
    'views': 5
}

# 修正したコード
published_at_str = article["published_at"].strftime('%Y年%m月%d日 %H:%M') if isinstance(article["published_at"], datetime) else str(article["published_at"])

print(f"元の値: {article['published_at']}")
print(f"フォーマット済み: {published_at_str}")
print(f"型: {type(published_at_str)}")

# テンプレートに埋め込むテスト
article_html = f'''
<div class="article-meta">
    <span class="badge bg-info">{article["source"]}</span>
    <span class="text-muted ms-3">{published_at_str}</span>
    <span class="text-muted ms-3">閲覧: {article["views"]}</span>
</div>
'''

print("\nHTML出力:")
print(article_html)
