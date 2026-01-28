import feedparser
from pprint import pprint

# Google News フィード取得
url = "https://news.google.com/rss/search?q=ゲーム&ceid=JP:ja"
feed = feedparser.parse(url)

print(f"=== フィード情報 ===")
print(f"Title: {feed.feed.get('title', 'N/A')}")
print(f"\n=== 最初の3つの記事構造 ===\n")

for i, entry in enumerate(feed.entries[:3]):
    print(f"\n--- 記事 {i+1} ---")
    print(f"Title: {entry.get('title', 'N/A')[:60]}...")
    print(f"\n利用可能な属性:")
    
    # すべての属性をチェック
    for key in entry.keys():
        if key not in ['title', 'link', 'summary']:  # 長い属性を除外
            value = entry[key]
            if isinstance(value, str):
                print(f"  - {key}: {value[:80]}..." if len(str(value)) > 80 else f"  - {key}: {value}")
            else:
                print(f"  - {key}: {type(value).__name__}")
    
    # 特に media_* と image* をチェック
    print("\nメディア関連:")
    for attr in ['media_content', 'media_thumbnail', 'image', 'media_credit']:
        if hasattr(entry, attr):
            print(f"  ✓ {attr}: {getattr(entry, attr)}")
    
    # summary を調べる
    if hasattr(entry, 'summary'):
        summary = entry.summary
        if '<img' in summary:
            print(f"\n✓ summary に画像タグあり: {summary.count('<img')} 個")
