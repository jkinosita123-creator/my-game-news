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
from difflib import SequenceMatcher
import html

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

    # プラットフォーム・カテゴリ定義
    CATEGORY_KEYWORDS = {
        'Switch': {'keywords': ['Switch', 'Nintendo Switch', 'ニンテンドースイッチ'], 'tag': 'switch', 'label': 'Switch'},
        'PS5': {'keywords': ['PS5', 'PlayStation 5', 'プレステ5'], 'tag': 'ps5', 'label': 'PS5'},
        'Xbox': {'keywords': ['Xbox', 'XSX'], 'tag': 'xbox', 'label': 'Xbox'},
        'PC': {'keywords': ['PC', 'Steam', 'ゲーミングPC'], 'tag': 'pc', 'label': 'PC'},
        'Steam': {'keywords': ['Steam'], 'tag': 'steam', 'label': 'Steam'},
        'Nintendo': {'keywords': ['Nintendo'], 'tag': 'nintendo', 'label': 'Nintendo'},
    }

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.keywords = self._build_keyword_map()
        self.amazon_tracking_id = config['affiliate']['amazon']['tracking_id']

    def _build_keyword_map(self) -> Dict[str, Dict[str, Any]]:
        """キーワードマップを構築"""
        keyword_map = {}
        for kw_config in self.config['keywords'].get('affiliate_targets', []):
            keyword = kw_config['keyword']
            keyword_map[keyword] = kw_config
        return keyword_map

    def get_category_tags(self, title: str) -> List[Dict[str, str]]:
        """タイトルから自動カテゴリタグを抽出"""
        tags = []
        for category, config in self.CATEGORY_KEYWORDS.items():
            for keyword in config['keywords']:
                if keyword.lower() in title.lower():
                    tags.append({
                        'tag': config['tag'],
                        'label': config['label']
                    })
                    break
        return tags

    def generate_fallback_image_url(self, title: str) -> str:
        """タイトルからキーワードを抽出してLoremFlickr画像URLを生成"""
        import urllib.parse
        
        # タイトルからキーワード抽出
        keywords = []
        
        # プラットフォーム名を優先
        platforms = ['Switch', 'PS5', 'PS4', 'Xbox', 'Steam', 'Nintendo', 'PC']
        for platform in platforms:
            if platform.lower() in title.lower():
                keywords.append('game')
                break
        
        # ゲーム/アニメ関連キーワードをチェック
        game_keywords = ['ゲーム', 'ソフト', 'RPG', 'アクション', 'シューティング', 'スポーツ']
        anime_keywords = ['アニメ', 'キャラ', '声優', 'マンガ']
        girl_keywords = ['女の子', 'キャラクター', 'グッズ']
        
        for kw in game_keywords:
            if kw in title:
                keywords.append('game')
                break
        
        for kw in anime_keywords:
            if kw in title:
                keywords.append('anime')
                break
        
        for kw in girl_keywords:
            if kw in title:
                keywords.append('girl')
                break
        
        # デフォルトキーワード
        if not keywords:
            keywords = ['game', 'anime']
        
        # キーワード文字列を生成
        keyword_string = ','.join(keywords[:3])
        
        # LoremFlickr URLを生成（常にランダム画像）
        return f"https://loremflickr.com/800/600/{keyword_string}/all?random={hash(title) % 10000}"

    def generate_amazon_search_link(self, title: str) -> str:
        """記事タイトルでAmazon検索リンクを生成（最適化版）"""
        import urllib.parse

        # タイトルから括弧内の情報を除去
        title_clean = re.sub(r'[（(].*[）)]', '', title).strip()
        title_clean = re.sub(r'[【].*[】]', '', title_clean).strip()
        title_clean = re.sub(r'[『].*[』]', '', title_clean).strip()

        # 意味のある検索キーワードを抽出
        keywords = []
        
        # プラットフォームキーワードをチェック
        platforms = ['Switch', 'PS5', 'PS4', 'Xbox', 'Steam', 'Nintendo', 'PC']
        for platform in platforms:
            if platform in title_clean:
                keywords.append(platform)
                break
        
        # ゲーム関連キーワードをチェック
        game_keywords = ['ゲーム', 'ソフト', 'タイトル', '発売', '予約', '限定版']
        for kw in game_keywords:
            if kw in title_clean and len(' '.join(keywords + [kw])) <= 20:
                keywords.append(kw)
                break
        
        # キーワードが見つからない場合は最初の単語を使用
        if not keywords:
            words = re.split(r'[\s　・]', title_clean)
            keywords = [word for word in words[:2] if word]
        
        # 検索クエリを構築（最大20文字程度）
        search_query = ' '.join(keywords)
        if len(search_query) > 20:
            search_query = search_query[:20].strip()
        
        if not search_query.strip():
            search_query = "ゲーム"
        
        encoded_query = urllib.parse.quote(search_query.strip())
        return f"https://www.amazon.co.jp/s?k={encoded_query}&tag={self.amazon_tracking_id}"

    def is_hot_news(self, title: str) -> bool:
        """タイトルに「爆売れ」キーワードが含まれるか判定"""
        hot_keywords = ["予約開始", "限定", "特典", "発売日決定"]
        return any(keyword in title for keyword in hot_keywords)

    def process_title(self, title: str, article_id: Optional[int] = None) -> str:
        """タイトルにアフィリエイトリンクを埋め込む"""
        processed_title = title

        for keyword, keyword_config in self.keywords.items():
            if keyword.lower() in processed_title.lower():
                affiliate_links = keyword_config.get('affiliate_links', [])

                for link_config in affiliate_links:
                    link_type = link_config.get('type', '')

                    if link_type == 'amazon' and self.config['affiliate'].get('amazon', {}).get('enabled'):
                        affiliate_url = self._build_amazon_link(
                            link_config['url_pattern'],
                            self.amazon_tracking_id
                        )
                        processed_title = self._inject_link(
                            processed_title, keyword, affiliate_url
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
                        processed_title = self._inject_link(
                            processed_title, keyword, affiliate_url
                        )

                        if article_id:
                            DB.save_affiliate_link(
                                article_id, keyword, 'rakuten', None, affiliate_url
                            )

        return processed_title

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
                            self.amazon_tracking_id
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


def generate_ogp_meta_tags(title: str, description: str, image_url: str, url: str) -> str:
    """OGPメタタグを生成"""
    tags = f'''    <meta property="og:title" content="{html.escape(title[:60])}" />
    <meta property="og:description" content="{html.escape(description[:120])}" />
    <meta property="og:image" content="{image_url}" />
    <meta property="og:url" content="{url}" />
    <meta property="og:type" content="website" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="{html.escape(title[:60])}" />
    <meta name="twitter:description" content="{html.escape(description[:120])}" />
    <meta name="twitter:image" content="{image_url}" />'''
    return tags


def remove_duplicate_articles(articles: List[Dict[str, Any]], similarity_threshold: float = 0.85) -> List[Dict[str, Any]]:
    """タイトルが酷似している記事を除去（最新のもののみ残す）"""
    if not articles:
        return articles
    
    filtered_articles = []
    for article in articles:
        is_duplicate = False
        for filtered_article in filtered_articles:
            # 相似度計算
            similarity = SequenceMatcher(None, article['title'], filtered_article['title']).ratio()
            if similarity > similarity_threshold:
                # 新しい記事なら置き換え、古い記事なら無視
                if article['published_at'] > filtered_article['published_at']:
                    filtered_articles.remove(filtered_article)
                    filtered_articles.append(article)
                is_duplicate = True
                break
        
        if not is_duplicate:
            filtered_articles.append(article)
    
    return filtered_articles


@app.get("/", response_class=HTMLResponse)
async def index(page: int = Query(1, ge=1)):
    """トップページ"""
    limit = 20
    offset = (page - 1) * limit

    articles = db.get_recent_articles(limit=limit + 10, offset=offset)
    
    # 重複記事を除去
    articles = remove_duplicate_articles(articles)
    articles = articles[:limit]
    
    total_articles = db.get_total_articles()
    total_pages = (total_articles + limit - 1) // limit

    article_html = ""
    first_image = None
    
    for article in articles:
        # 画像取得: DB画像またはLoremFlickr フォールバック
        if article["image_url"]:
            image_tag = f'<img src="{article["image_url"]}" alt="{article["title"]}" class="card-img-top">'
            image_url = article["image_url"]
        else:
            fallback_url = affiliate_engine.generate_fallback_image_url(article["title"])
            image_tag = f'<img src="{fallback_url}" alt="{article["title"]}" class="card-img-top">'
            image_url = fallback_url
        
        # 最初の記事の画像をOGPで使用
        if first_image is None:
            first_image = image_url

        # タイトルを処理（アフィリエイトリンク埋め込み）
        processed_title = affiliate_engine.process_title(article["title"], article["id"])

        # ホットニュース判定
        hot_label = ""
        if affiliate_engine.is_hot_news(article["title"]):
            hot_label = '<div class="hot-news-label">🔥お宝情報！</div>'

        # カテゴリタグを取得
        category_tags = affiliate_engine.get_category_tags(article["title"])
        category_html = ""
        if category_tags:
            category_html = "<div class='mb-2'>"
            for tag in category_tags:
                category_html += f'<span class="category-tag {tag["tag"]}">{tag["label"]}</span>'
            category_html += "</div>"

        # Amazon検索リンク生成
        amazon_search_url = affiliate_engine.generate_amazon_search_link(article["title"])
        amazon_ranking_url = f"https://www.amazon.co.jp/gp/bestsellers/videogames/ref=zg_bs_nav_0?tag={affiliate_engine.amazon_tracking_id}"

        article_html += f'''
        <div class="article-card-wrapper">
            <div class="card h-100 article-card">
                {hot_label}
                {image_tag}
                <div class="card-body">
                    <small class="text-muted badge bg-info">{article["source"]}</small>
                    {category_html}
                    <h5 class="card-title mt-2">{processed_title}</h5>
                    <p class="card-text text-muted text-clamp">{article["content"][:100]}...</p>
                    <div class="d-flex flex-column gap-2 mt-auto">
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

    # トップページのOGPメタタグ
    ogp_tags = generate_ogp_meta_tags(
        title=config['site']['name'],
        description=config['site']['description'],
        image_url=first_image or "https://loremflickr.com/800/600/game,anime",
        url=config['site']['base_url']
    )

    html_content = template.replace(
        '<!-- OGP_META_TAGS -->',
        ogp_tags
    ).replace(
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

    return affiliate_engine.inject_adsense(html_content)


@app.get("/article/{article_id}", response_class=HTMLResponse)
async def article_detail(article_id: int):
    """記事詳細ページ"""
    article = db.get_article_by_id(article_id)

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    db.increment_views(article_id)

    content = article['content']
    content_with_affiliate = affiliate_engine.process_content(content, article_id)

    # タイトルを処理
    processed_title = affiliate_engine.process_title(article["title"], article_id)

    # 画像取得
    if article["image_url"]:
        image_url = article["image_url"]
    else:
        image_url = affiliate_engine.generate_fallback_image_url(article["title"])

    # カテゴリタグを取得
    category_tags = affiliate_engine.get_category_tags(article["title"])
    category_html = ""
    if category_tags:
        category_html = "<div class='mb-3'>"
        for tag in category_tags:
            category_html += f'<span class="category-tag {tag["tag"]}">{tag["label"]}</span>'
        category_html += "</div>"

    # Amazon検索リンク生成
    amazon_search_url = affiliate_engine.generate_amazon_search_link(article["title"])
    amazon_ranking_url = f"https://www.amazon.co.jp/gp/bestsellers/videogames/ref=zg_bs_nav_0?tag={affiliate_engine.amazon_tracking_id}"

    article_html = f'''
    <div class="container mt-5">
        <article class="article-detail">
            <h1>{processed_title}</h1>
            {category_html}
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
                <a href="{amazon_search_url}" class="btn btn-warning me-2 mb-2" target="_blank" rel="noopener noreferrer">
                    🛒 Amazonで関連商品をチェック
                </a>
                <a href="{amazon_ranking_url}" class="btn btn-success me-2 mb-2" target="_blank" rel="noopener noreferrer">
                    🏆 売れ筋ランキング
                </a>
                <a href="{article["url"]}" class="btn btn-primary me-2 mb-2" target="_blank">元の記事</a>
                <a href="/" class="btn btn-secondary">トップへ戻る</a>
            </div>
        </article>
    </div>
    '''

    with open('templates/layout.html', 'r', encoding='utf-8') as f:
        template = f.read()

    # 記事詳細ページのOGPメタタグ
    ogp_tags = generate_ogp_meta_tags(
        title=article["title"],
        description=article["content"][:120],
        image_url=image_url,
        url=f"{config['site']['base_url']}article/{article_id}"
    )

    html_content = template.replace(
        '<!-- OGP_META_TAGS -->',
        ogp_tags
    ).replace(
        '<!-- ARTICLES_PLACEHOLDER -->',
        article_html
    ).replace(
        '{{ site_name }}',
        config['site']['name']
    ).replace(
        '{{ site_description }}',
        config['site']['description']
    )

    return affiliate_engine.inject_adsense(html_content)


@app.get("/search", response_class=HTMLResponse)
async def search(q: str = Query(...)):
    """検索ページ"""
    articles = db.search_articles(q, limit=50)
    
    # 重複記事を除去
    articles = remove_duplicate_articles(articles)

    article_html = ""
    first_image = None
    
    for article in articles:
        # 画像取得
        if article["image_url"]:
            image_tag = f'<img src="{article["image_url"]}" alt="{article["title"]}" class="card-img-top">'
            image_url = article["image_url"]
        else:
            fallback_url = affiliate_engine.generate_fallback_image_url(article["title"])
            image_tag = f'<img src="{fallback_url}" alt="{article["title"]}" class="card-img-top">'
            image_url = fallback_url
        
        if first_image is None:
            first_image = image_url

        # タイトルを処理（アフィリエイトリンク埋め込み）
        processed_title = affiliate_engine.process_title(article["title"], article["id"])

        # ホットニュース判定
        hot_label = ""
        if affiliate_engine.is_hot_news(article["title"]):
            hot_label = '<div class="hot-news-label">🔥お宝情報！</div>'

        # カテゴリタグを取得
        category_tags = affiliate_engine.get_category_tags(article["title"])
        category_html = ""
        if category_tags:
            category_html = "<div class='mb-2'>"
            for tag in category_tags:
                category_html += f'<span class="category-tag {tag["tag"]}">{tag["label"]}</span>'
            category_html += "</div>"

        # Amazon検索リンク生成
        amazon_search_url = affiliate_engine.generate_amazon_search_link(article["title"])
        amazon_ranking_url = f"https://www.amazon.co.jp/gp/bestsellers/videogames/ref=zg_bs_nav_0?tag={affiliate_engine.amazon_tracking_id}"

        article_html += f'''
        <div class="article-card-wrapper">
            <div class="card h-100 article-card">
                {hot_label}
                {image_tag}
                <div class="card-body">
                    <small class="text-muted badge bg-info">{article["source"]}</small>
                    {category_html}
                    <h5 class="card-title mt-2">{processed_title}</h5>
                    <p class="card-text text-muted text-clamp">{article["content"][:100]}...</p>
                    <div class="d-flex flex-column gap-2 mt-auto">
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

    with open('templates/layout.html', 'r', encoding='utf-8') as f:
        template = f.read()

    # 検索結果ページのOGPメタタグ
    ogp_tags = generate_ogp_meta_tags(
        title=f"検索: {q}",
        description=f"「{q}」の検索結果",
        image_url=first_image or "https://loremflickr.com/800/600/game,anime",
        url=f"{config['site']['base_url']}search?q={q}"
    )

    html_content = template.replace(
        '<!-- OGP_META_TAGS -->',
        ogp_tags
    ).replace(
        '<!-- ARTICLES_PLACEHOLDER -->',
        article_html if article_html else '<p class="text-center text-muted">検索結果がありません</p>'
    ).replace(
        '{{ site_name }}',
        config['site']['name']
    ).replace(
        '{{ site_description }}',
        config['site']['description']
    )

    return affiliate_engine.inject_adsense(html_content)


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
