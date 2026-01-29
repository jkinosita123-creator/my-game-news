"""
index ルートのエラーを直接テスト（サーバー外で）
"""
import sys
sys.path.insert(0, r'c:\Users\owner\Desktop\GameNewsProject')

import traceback
from models import DatabaseManager
from app import remove_duplicate_articles, AffiliateEngine, extract_main_keyword
import yaml
from datetime import datetime

with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

print("=" * 70)
print("index() ロジック完全テスト")
print("=" * 70)

try:
    db = DatabaseManager(config['database']['path'])
    affiliate_engine = AffiliateEngine(config)
    
    page = 1
    limit = 20
    offset = (page - 1) * limit
    
    print(f"\n[1] 記事取得")
    articles = db.get_recent_articles(limit=limit + 10, offset=offset)
    print(f"    OK: {len(articles)}件")
    
    print(f"\n[2] 重複除去")
    articles = remove_duplicate_articles(articles)
    print(f"    OK: {len(articles)}件")
    
    articles = articles[:limit]
    print(f"    OK: スライス後 {len(articles)}件")
    
    print(f"\n[3] 総記事数")
    total_articles = db.get_total_articles()
    total_pages = (total_articles + limit - 1) // limit
    print(f"    OK: total={total_articles}, pages={total_pages}")
    
    print(f"\n[4] HTML生成")
    article_html = ""
    image_keywords = ['game', 'anime', 'girl', 'manga', 'cute', 'kawaii', 'beautiful', 'art']
    
    for idx, article in enumerate(articles, 1):
        title_keyword = extract_main_keyword(article["title"])
        image_keyword = image_keywords[(idx - 1) % len(image_keywords)]
        image_url = f'https://loremflickr.com/400/300/{image_keyword},anime,girl/all?random={idx * 1000}'
        image_tag = f'<img src="{image_url}" alt="{article["title"]}" class="card-img-top">'
        
        processed_title = affiliate_engine.process_title(article["title"], article["id"])
        
        hot_label = ""
        if affiliate_engine.is_hot_news(article["title"]):
            hot_label = '<div class="hot-news-label">🔥お宝情報！</div>'
        
        category_tags = affiliate_engine.get_category_tags(article["title"])
        category_html = ""
        if category_tags:
            category_html = "<div class='mb-2'>"
            for tag in category_tags:
                category_html += f'<span class="category-tag {tag["tag"]}">{tag["label"]}</span>'
            category_html += "</div>"
        
        amazon_search_url = affiliate_engine.generate_amazon_search_link(article["title"])
        amazon_ranking_url = "https://www.amazon.co.jp/gp/bestsellers/videogames/ref=zg_bs_nav_0"
        
        article_html += f'''
        <div class="col-12 col-md-6 col-lg-4 mb-4 article-card-wrapper">
            <div class="card h-100 article-card">
                {hot_label}
                {image_tag}
                <div class="card-body">
                    <small class="text-muted badge bg-info">{article["source"]}</small>
                    {category_html}
                    <h5 class="card-title mt-2">{processed_title}</h5>
                    <p class="card-text text-muted">{article["content"][:100]}...</p>
                    <div class="d-flex flex-column gap-2 mt-3">
                        <div class="btn-group w-100" role="group">
                            <a href="{amazon_search_url}" class="btn btn-sm btn-warning flex-fill" target="_blank" rel="noopener noreferrer">
                                🛒 Amazonでチェック
                            </a>
                            <a href="/article/{article["id"]}" class="btn btn-sm btn-primary">詳細</a>
                        </div>
                        <a href="{amazon_ranking_url}" class="btn btn-sm btn-success w-100" target="_blank" rel="noopener noreferrer">
                            🏆 売れ筋ランキング
                        </a>
                    </div>
                </div>
            </div>
        </div>
        '''
    
    print(f"    OK: HTML生成 {len(article_html)}文字")
    
    print(f"\n[5] ページネーション HTML")
    pagination_html = ""
    if total_pages > 1:
        pagination_html = f'''
        <nav aria-label="Page navigation" class="mt-5">
            <ul class="pagination justify-content-center">
        '''
        if page > 1:
            pagination_html += f'<li class="page-item"><a class="page-link" href="/?page={page-1}">前へ</a></li>'

        for p in range(max(1, page - 2), min(total_pages + 1, page + 3)):
            active = "active" if p == page else ""
            pagination_html += f'<li class="page-item {active}"><a class="page-link" href="/?page={p}">{p}</a></li>'

        if page < total_pages:
            pagination_html += f'<li class="page-item"><a class="page-link" href="/?page={page+1}">次へ</a></li>'

        pagination_html += '''
            </ul>
        </nav>
        '''
    
    print(f"    OK: {len(pagination_html)}文字")
    
    print(f"\n[6] テンプレート読み込み")
    with open('templates/layout.html', 'r', encoding='utf-8') as f:
        template = f.read()
    print(f"    OK: {len(template)}文字")
    
    print(f"\n[7] テンプレート置換")
    html = template.replace(
        '<!-- ARTICLES_PLACEHOLDER -->',
        article_html
    ).replace(
        '<!-- PAGINATION_PLACEHOLDER -->',
        pagination_html
    ).replace(
        '{{ site_name }}',
        config['site']['name']
    ).replace(
        '{{ site_description }}',
        config['site']['description']
    ).replace(
        '{{ total_articles }}',
        str(total_articles)
    )
    
    print(f"    OK: 最終HTML {len(html)}文字")
    
    print(f"\n[8] AdSense埋め込み")
    final_html = affiliate_engine.inject_adsense(html)
    print(f"    OK: {len(final_html)}文字")
    
    print(f"\n✅ すべてのステップが成功しました")
    print(f"   最終HTML: {len(final_html)} bytes")
    
except Exception as e:
    print(f"\n❌ エラー: {type(e).__name__}: {e}")
    print("\nトレースバック:")
    traceback.print_exc()
    sys.exit(1)
