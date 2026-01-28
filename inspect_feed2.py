import feedparser

# Google News フィード取得
url = "https://news.google.com/rss/search?q=ゲーム&ceid=JP:ja"
feed = feedparser.parse(url)

print("=== 最初の記事の詳細 ===\n")
entry = feed.entries[0]

print(f"Title: {entry.title}\n")

print("=== Links ===")
for link in entry.get('links', []):
    print(f"  - {link}")

print("\n=== Summary ===")
summary = entry.get('summary', '')
print(summary[:500] if summary else "なし")

print("\n=== Summary Detail ===")
summary_detail = entry.get('summary_detail', {})
print(f"Type: {summary_detail.get('type')}")
print(f"Language: {summary_detail.get('language')}")
print(f"Value (最初の300文字): {summary_detail.get('value', '')[:300]}")

print("\n=== Source ===")
source = entry.get('source', {})
for key, value in source.items():
    if key != 'links':
        print(f"  {key}: {value}")
