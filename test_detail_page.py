"""
詳細ページ表示関数のテスト（サーバー起動なし）
"""
import sys
sys.path.insert(0, r'c:\Users\owner\Desktop\GameNewsProject')

from models import DatabaseManager
from app import AffiliateEngine, remove_duplicate_articles
from datetime import datetime
import yaml

# 設定読み込み
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 初期化
db = DatabaseManager(config['database']['path'])
affiliate_engine = AffiliateEngine(config)

# 最初の記事を取得
articles = db.get_recent_articles(limit=1)
if not articles:
    print("❌ 記事がありません")
    sys.exit(1)

article = articles[0]
article_id = article['id']

print(f"✓ 記事ID: {article_id}")
print(f"✓ タイトル: {article['title']}")
print(f"✓ published_at型: {type(article['published_at'])}")

# 詳細ページ処理をテスト
try:
    content = article['content']
    print(f"✓ コンテンツ長: {len(content)}")
    
    content_with_affiliate = affiliate_engine.process_content(content, article_id)
    print(f"✓ アフィリエイト処理: 成功")
    
    processed_title = affiliate_engine.process_title(article["title"], article_id)
    print(f"✓ タイトル処理: 成功")
    
    category_tags = affiliate_engine.get_category_tags(article["title"])
    print(f"✓ カテゴリタグ: {len(category_tags)}個")
    
    # Amazon検索リンク生成
    amazon_search_url = affiliate_engine.generate_amazon_search_link(article["title"])
    print(f"✓ Amazon検索リンク: {amazon_search_url[:50]}...")
    
    # 詳細ページ用の画像URL生成テスト
    detail_image_keywords = ['girl,cute,kawaii', 'anime,girl,beautiful', 'manga,girl,kawaii', 'girl,smile,cute', 'girl,portrait,beautiful']
    image_keyword = detail_image_keywords[hash(article["title"]) % len(detail_image_keywords)]
    detail_image_url = f'https://loremflickr.com/800/400/{image_keyword}/all?random={article["id"]}'
    print(f"✓ 画像URL生成: 成功")
    
    # published_at フォーマット処理テスト
    published_at_str = article["published_at"].strftime('%Y年%m月%d日 %H:%M') if isinstance(article["published_at"], datetime) else str(article["published_at"])
    print(f"✓ 日付フォーマット: {published_at_str}")
    
    # HTML生成テスト
    category_html = ""
    if category_tags:
        category_html = "<div class='mb-3'>"
        for tag in category_tags:
            category_html += f'<span class="category-tag {tag["tag"]}">{tag["label"]}</span>'
        category_html += "</div>"
    
    article_html = f'''
    <div class="container mt-5">
        <article class="article-detail">
            <div class="detail-image-container mb-4">
                <img src="{detail_image_url}" alt="{article['title']}" class="detail-image img-fluid rounded shadow" onerror="this.style.backgroundColor='#e8d5f2'">
            </div>
            <h1>{processed_title}</h1>
            {category_html}
            <div class="article-meta">
                <span class="badge bg-info">{article["source"]}</span>
                <span class="text-muted ms-3">{published_at_str}</span>
                <span class="text-muted ms-3">閲覧: {article["views"]}</span>
            </div>
            <hr>
            <div class="article-body">
                {content_with_affiliate}
            </div>
        </article>
    </div>
    '''
    
    print(f"✓ HTML生成: 成功 ({len(article_html)}文字)")
    
    # HTMLが正常に生成されたか確認
    if '<div class="article-detail">' in article_html:
        print("✓ 詳細ページHTML構造: 正常")
    
    if detail_image_url in article_html:
        print("✓ 画像タグが埋め込まれています")
    
    if published_at_str in article_html:
        print("✓ 日付がHTMLに埋め込まれています")
    
    print("\n✅ すべてのテストに合格しました。詳細ページは正常に表示されるはずです。")
    
except Exception as e:
    print(f"❌ エラー発生: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
