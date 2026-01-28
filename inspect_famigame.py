import feedparser

# ファミゲームフィード取得
url = "https://news.denfaminicogamer.jp/feed"
feed = feedparser.parse(url)

print("=== 最初の記事の詳細 ===\n")
entry = feed.entries[0]

print(f"Title: {entry.title[:80]}\n")

print("=== Summary ===")
summary = entry.get('summary', '')
print(summary[:1000])

print("\n=== img タグの数 ===")
import re
img_count = len(re.findall(r'<img', summary))
print(f"Found: {img_count} img tags")

if '<img' in summary:
    img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', summary)
    if img_match:
        print(f"\n✓ 画像URL: {img_match.group(1)[:80]}")
