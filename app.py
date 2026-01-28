from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import yaml
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging
from models import DatabaseManager, Article
from crawler import RSSCrawler
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 設定読み込み
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

app = FastAPI(
    title=config['site']['name'],
    description=config['site']['description']
)

db = DatabaseManager(config['database']['path'])
crawler = RSSCrawler('config.yaml')

# グローバル設定
SITE_CONFIG = config
DB = db

# クローラーをバックグラウンドで開始
crawler.start_scheduler_background()


class AffiliateEngine:
    """アフィリエイトリンク埋め込みエンジン"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.keywords = self._build_keyword_map()

    def _build_keyword_map(self) -> Dict[str, Dict[str, Any]]:
        """キーワードマップを構築"""
        keyword_map = {}
        for kw_config in self.config['keywords'].get('affiliate_targets', []):
            keyword = kw_config['keyword']
            keyword_map[keyword] = kw_config
        return keyword_map

    def process_content(self, content: str, article_id: Optional[int] = None) -> str:
        """コンテンツにアフィリエイトリンクを埋め込む"""
        processed_content = content

        for keyword, keyword_config in self.keywords.items():
            if keyword.lower() in content.lower():
                affiliate_links = keyword_config.get('affiliate_links', [])

                for link_config in affiliate_links:
                    link_type = link_config.get('type', '')

                    if link_type == 'amazon' and self.config['affiliate'].get('amazon', {}).get('enabled'):
                        affiliate_url = self._build_amazon_link(
                            link_config['url_pattern'],
                            self.config['affiliate']['amazon']['tracking_id']
                        )
                        processed_content = self._inject_link(
                            processed_content, keyword, affiliate_url
                        )

                        if article_id:
                            DB.save_affiliate_link(
                                article_id, keyword, 'amazon', None, affiliate_url
                            )

                    elif link_type == 'rakuten' and self.config['affiliate'].get('rakuten', {}).get('enabled'):
                        affiliate_url = self._build_rakuten_link(
                            link_config['url_pattern'],
                            self.config['affiliate']['rakuten']['affiliate_id']
                        )
                        processed_content = self._inject_link(
                            processed_content, keyword, affiliate_url
                        )

                        if article_id:
                            DB.save_affiliate_link(
                                article_id, keyword, 'rakuten', None, affiliate_url
                            )

        return processed_content

    def _build_amazon_link(self, base_url: str, tracking_id: str) -> str:
        """Amazon アフィリエイトリンクを構築"""
        separator = '&' if '?' in base_url else '?'
        return f"{base_url}{separator}tag={tracking_id}"

    def _build_rakuten_link(self, base_url: str, affiliate_id: str) -> str:
        """楽天アフィリエイトリンクを構築"""
        separator = '&' if '?' in base_url else '?'
        return f"{base_url}{separator}aid={affiliate_id}"

    def _inject_link(self, content: str, keyword: str, affiliate_url: str) -> str:
        """コンテンツにリンクを注入（最初の1回のみ）"""
        pattern = rf'(?<!<a[^>]*>\s*)\b{re.escape(keyword)}\b(?!</a>)'
        replacement = f'<a href="{affiliate_url}" target="_blank" rel="noopener noreferrer">{keyword}</a>'
        return re.sub(pattern, replacement, content, count=1, flags=re.IGNORECASE)

    def inject_adsense(self, html_content: str) -> str:
        """Google AdSense広告を注入"""
        if not self.config['affiliate'].get('google_adsense', {}).get('enabled'):
            return html_content

        publisher_id = self.config['affiliate']['google_adsense'].get('publisher_id')
        ad_slot = self.config['affiliate']['google_adsense'].get('ad_slot')

        ad_code = f'''
<!-- Google AdSense -->
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={publisher_id}"
     crossorigin="anonymous"></script>
<!-- Article Ad -->
<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="{publisher_id}"
     data-ad-slot="{ad_slot}"
     data-ad-format="auto"
     data-full-width-responsive="true"></ins>
<script>
     (adsbygoogle = window.adsbygoogle || []).push({{}});
</script>
        '''

        return html_content.replace('<!-- AD_PLACEHOLDER -->', ad_code)


affiliate_engine = AffiliateEngine(config)


@app.get("/", response_class=HTMLResponse)
async def index(page: int = Query(1, ge=1)):
    """トップページ"""
    limit = 20
    offset = (page - 1) * limit

    articles = db.get_recent_articles(limit=limit, offset=offset)
    total_articles = db.get_total_articles()
    total_pages = (total_articles + limit - 1) // limit

    article_html = ""
    for article in articles:
        image_tag = f'<img src="{article["image_url"]}" alt="{article["title"]}" class="card-img-top">' if article["image_url"] else '<div class="placeholder-image"></div>'

        article_html += f'''
        <div class="col-md-6 col-lg-4 mb-4">
            <div class="card h-100 article-card">
                {image_tag}
                <div class="card-body">
                    <small class="text-muted badge bg-info">{article["source"]}</small>
                    <h5 class="card-title mt-2">{article["title"]}</h5>
                    <p class="card-text text-muted">{article["content"][:100]}...</p>
                    <div class="d-flex justify-content-between align-items-center mt-3">
                        <small class="text-muted">{article["published_at"][:10]}</small>
                        <a href="/article/{article["id"]}" class="btn btn-sm btn-primary">詳細</a>
                    </div>
                </div>
            </div>
        </div>
        '''

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

    with open('templates/layout.html', 'r', encoding='utf-8') as f:
        template = f.read()

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

    return affiliate_engine.inject_adsense(html)


@app.get("/article/{article_id}", response_class=HTMLResponse)
async def article_detail(article_id: int):
    """記事詳細ページ"""
    article = db.get_article_by_id(article_id)

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    db.increment_views(article_id)

    content = article['content']
    content_with_affiliate = affiliate_engine.process_content(content, article_id)

    article_html = f'''
    <div class="container mt-5">
        <article class="article-detail">
            <h1>{article["title"]}</h1>
            <div class="article-meta">
                <span class="badge bg-info">{article["source"]}</span>
                <span class="text-muted ms-3">{article["published_at"]}</span>
                <span class="text-muted ms-3">閲覧: {article["views"]}</span>
            </div>
            <hr>
            <div class="article-body">
                {content_with_affiliate}
            </div>
            <hr>
            <div class="article-actions">
                <a href="{article["url"]}" class="btn btn-primary" target="_blank">元の記事</a>
                <a href="/" class="btn btn-secondary">トップへ戻る</a>
            </div>
        </article>
    </div>
    '''

    with open('templates/layout.html', 'r', encoding='utf-8') as f:
        template = f.read()

    html = template.replace(
        '<!-- ARTICLES_PLACEHOLDER -->',
        article_html
    ).replace(
        '{{ site_name }}',
        config['site']['name']
    ).replace(
        '{{ site_description }}',
        config['site']['description']
    )

    return affiliate_engine.inject_adsense(html)


@app.get("/search", response_class=HTMLResponse)
async def search(q: str = Query(...)):
    """検索ページ"""
    articles = db.search_articles(q, limit=50)

    article_html = ""
    for article in articles:
        image_tag = f'<img src="{article["image_url"]}" alt="{article["title"]}" class="card-img-top">' if article["image_url"] else '<div class="placeholder-image"></div>'

        article_html += f'''
        <div class="col-md-6 col-lg-4 mb-4">
            <div class="card h-100 article-card">
                {image_tag}
                <div class="card-body">
                    <small class="text-muted badge bg-info">{article["source"]}</small>
                    <h5 class="card-title mt-2">{article["title"]}</h5>
                    <p class="card-text text-muted">{article["content"][:100]}...</p>
                    <a href="/article/{article["id"]}" class="btn btn-sm btn-primary">詳細</a>
                </div>
            </div>
        </div>
        '''

    with open('templates/layout.html', 'r', encoding='utf-8') as f:
        template = f.read()

    html = template.replace(
        '<!-- ARTICLES_PLACEHOLDER -->',
        article_html if article_html else '<p class="text-center text-muted">検索結果がありません</p>'
    ).replace(
        '{{ site_name }}',
        config['site']['name']
    ).replace(
        '{{ site_description }}',
        config['site']['description']
    )

    return affiliate_engine.inject_adsense(html)


@app.get("/api/articles")
async def api_articles(limit: int = 20, offset: int = 0, source: Optional[str] = None):
    """API: 記事一覧"""
    articles = db.get_recent_articles(limit=limit, offset=offset, source=source)
    total = db.get_total_articles()
    return {
        "articles": articles,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@app.get("/api/stats")
async def api_stats():
    """API: 統計情報"""
    total = db.get_total_articles()
    by_source = db.get_articles_by_source()

    return {
        "total_articles": total,
        "by_source": by_source,
        "site_name": config['site']['name'],
        "last_updated": datetime.now().isoformat()
    }


@app.post("/api/crawl")
async def api_crawl():
    """API: クローラーを手動実行"""
    try:
        crawler.crawl_all_feeds()
        return {"status": "success", "message": "Crawl completed"}
    except Exception as e:
        logger.error(f"Error during manual crawl: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    host = config['server'].get('host', '0.0.0.0')
    port = config['server'].get('port', 8000)
    workers = config['server'].get('workers', 4)

    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        workers=workers,
        reload=config['server'].get('reload', True)
    )
