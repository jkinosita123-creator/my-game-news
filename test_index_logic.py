"""
index() ルートの処理をスタンドアロンでテスト
"""
import sys
sys.path.insert(0, r'c:\Users\owner\Desktop\GameNewsProject')

from models import DatabaseManager
from app import remove_duplicate_articles, AffiliateEngine, extract_main_keyword
import yaml
from datetime import datetime
import traceback

# 設定読み込み
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

print("=" * 70)
print("トップページロジックのテスト（index() ルート）")
print("=" * 70)

try:
    db = DatabaseManager(config['database']['path'])
    affiliate_engine = AffiliateEngine(config)
    
    # ページング パラメータ
    page = 1
    limit = 20
    offset = (page - 1) * limit
    
    print(f"\n[1] DB から記事を取得 (limit={limit+10}, offset={offset})")
    articles = db.get_recent_articles(limit=limit + 10, offset=offset)
    print(f"    取得数: {len(articles)}")
    if articles:
        print(f"    最初の記事: {articles[0]['title'][:50]}")
        print(f"    published_at 型: {type(articles[0]['published_at'])}")
    
    print(f"\n[2] 重複除去")
    articles_filtered = remove_duplicate_articles(articles)
    articles_filtered = articles_filtered[:limit]
    print(f"    フィルタ後: {len(articles_filtered)}")
    
    print(f"\n[3] 総記事数を取得")
    total_articles = db.get_total_articles()
    total_pages = (total_articles + limit - 1) // limit
    print(f"    total_articles: {total_articles}")
    print(f"    total_pages: {total_pages}")
    
    print(f"\n[4] 記事ごとの処理をテスト（最初の1記事のみ）")
    for idx, article in enumerate(articles_filtered[:1], 1):
        print(f"\n    記事 #{idx}")
        
        title_keyword = extract_main_keyword(article["title"])
        print(f"      title_keyword: {title_keyword}")
        
        processed_title = affiliate_engine.process_title(article["title"], article["id"])
        print(f"      processed_title: {processed_title[:50]}")
        
        is_hot = affiliate_engine.is_hot_news(article["title"])
        print(f"      is_hot_news: {is_hot}")
        
        tags = affiliate_engine.get_category_tags(article["title"])
        print(f"      category_tags: {len(tags)}")
        
        amazon_url = affiliate_engine.generate_amazon_search_link(article["title"])
        print(f"      amazon_search_url: {amazon_url[:70]}...")
    
    print(f"\n[5] テンプレート置換のテスト")
    with open('templates/layout.html', 'r', encoding='utf-8') as f:
        template = f.read()
    print(f"    テンプレートサイズ: {len(template)} bytes")
    print(f"    '{{ site_name }}' が含まれている: {'{{ site_name }}' in template}")
    
    test_html = template.replace('{{ site_name }}', config['site']['name'])
    print(f"    置換後サイズ: {len(test_html)} bytes")
    
    print(f"\n✅ すべてのテストに成功しました")

except Exception as e:
    print(f"\n❌ エラー発生: {type(e).__name__}: {e}")
    print("\nトレースバック:")
    traceback.print_exc()
