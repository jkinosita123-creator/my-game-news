# Copilot Instructions for GameNewsProject

## Project Overview

This is a **high-speed game news affiliate site generator** using Python FastAPI. The system automatically crawls RSS feeds every hour, stores articles in SQLite, and monetizes through Google AdSense + Amazon/Rakuten affiliate link auto-injection.

**Key goal**: Generate game news sites configured via `config.yaml` to run multiple "fleet" (複数サイト) operations targeting ¥1M monthly revenue through speed-based content distribution and affiliate link monetization.

## Core Architecture

### Three Main Components

1. **`app.py` (FastAPI Server)**
   - Serves HTML/API endpoints for the website
   - `AffiliateEngine` class: keyword-based detection → automatic affiliate link injection
   - Injects Google AdSense ads via `affiliate_engine.inject_adsense()`
   - Routes:
     - `GET /` - Magazine-style homepage with pagination
     - `GET /article/{id}` - Article detail with affiliate links + views tracking
     - `GET /search?q=` - Full-text search across title/content
     - `GET /api/articles` - JSON article list
     - `POST /api/crawl` - Manual crawler trigger

2. **`crawler.py` (RSSCrawler)**
   - Scheduled background task (1-hour intervals by default)
   - `RSSCrawler.crawl_all_feeds()`: fetches all configured RSS feeds
   - Duplicate detection via `Article.hash_id` (MD5 of title+url)
   - Saves logs to `crawler_logs` table
   - Scheduled via `schedule` library + threading (not async)

3. **`models.py` (Database Layer)**
   - SQLite with three tables:
     - `articles` - stores crawled content (hash_id, title, url, source, image_url, views)
     - `affiliate_links` - tracks keyword→affiliate replacements
     - `crawler_logs` - execution history + error tracking
   - Key methods: `save_article()`, `get_recent_articles()`, `increment_views()`, `search_articles()`

### Data Flow

```
RSS Feeds (config.yaml)
    ↓
crawler.py (RSSCrawler.crawl_feed)
    ↓
models.py (DatabaseManager.save_article)
    ↓
SQLite (articles table)
    ↓
app.py (FastAPI routes)
    ↓
AffiliateEngine (keyword detection + link injection)
    ↓
HTML Response (with AdSense + affiliate links)
```

## Critical Configuration Pattern

**`config.yaml` is the entire system customization point:**

- `site.name`, `site.description` - affects all page titles
- `rss_feeds[]` - determines content sources (Google News, Famitsu, 4Gamer pre-populated)
- `affiliate.amazon.tracking_id`, `affiliate.rakuten.affiliate_id` - revenue identifiers
- `keywords.affiliate_targets[]` - keyword→URL mappings for link injection (e.g., "Switch" → Amazon/Rakuten product pages)
- `crawler.interval_minutes` - RSS polling frequency
- `server.workers` - FastAPI worker count

**To launch a new site**: Copy `config.yaml`, update `site.name`, RSS feeds, and affiliate IDs. Run with `uvicorn app:app --host 0.0.0.0 --port <new_port>`.

## Key Technical Patterns

### Affiliate Link Injection

- Located in `AffiliateEngine` class (app.py)
- Triggered on `GET /article/{id}` and `GET /`
- Process:
  1. Scan article content for keywords from `config.yaml` → `keywords.affiliate_targets[]`
  2. For each match, replace first occurrence with `<a href="affiliate_url">keyword</a>`
  3. Log replacement in `affiliate_links` table (article_id, keyword, link_type, affiliate_url)
  4. Append tracking ID via `_build_amazon_link()` or `_build_rakuten_link()`

### Duplicate Prevention

- `Article._generate_hash()`: MD5(title + url) → unique `hash_id`
- `DatabaseManager.article_exists(hash_id)` checks before saving
- Returns None on duplicate → crawler logs "already exists"

### Pagination & SEO

- Homepage shows 20 articles per page, sorted by `published_at DESC`
- URL pattern: `/?page=2`, `/?page=3` etc.
- Search filtering by source: `?source=Famitsu`

## Important Implementation Details

### Database Indexing

- `hash_id` indexed for fast duplicate checks
- `published_at` indexed for sorting (critical for homepage performance)
- `source` indexed for filtering

### Crawler Threading

- **Not async**: Uses `threading.Thread()` + `schedule` library
- Background thread loops `schedule.run_pending()` every 60 seconds
- Called via `crawler.start_scheduler_background()` in `app.py` startup
- Does NOT block FastAPI request handling

### Image Extraction

- `RSSCrawler.extract_image_url()` searches entry.media_content, entry.image, then returns None
- Fallback in template: `placeholder-image` div (purple gradient)

### Session Management

- `requests.Session()` in crawler for connection pooling
- User-Agent header set to bypass feed provider blocking

## Common Development Tasks

### Adding a New RSS Feed

1. Edit `config.yaml`:
   ```yaml
   rss_feeds:
     - url: "https://example.com/feed.xml"
       source: "SourceName"
       priority: 2
   ```
2. No code changes needed; crawler automatically discovers on next run

### Adding New Affiliate Keyword

1. Edit `config.yaml`:
   ```yaml
   keywords:
     affiliate_targets:
       - keyword: "限定版"
         product_type: "limited_edition"
         affiliate_links:
           - type: "amazon"
             url_pattern: "https://www.amazon.co.jp/s?k=限定版ゲーム"
   ```
2. Restart app; next crawl applies to new articles

### Debugging Affiliate Injection

- Check `affiliate_links` table for successful replacements
- Verify keyword exists in article content (case-insensitive search)
- Confirm `affiliate.amazon.enabled: true` in config

### Performance Optimization

- **Pagination limit**: Currently 20 articles/page; adjust in `index()` route (`limit = 20`)
- **Cleanup**: `crawler.py` deletes articles older than `cleanup_days` (default 30) every crawl
- **Worker threads**: Set `server.workers` (default 4); increase for high traffic

## File References for Quick Navigation

- **Database schema & queries**: [models.py](models.py) - `DatabaseManager` class
- **Affiliate logic**: [app.py](app.py) - `AffiliateEngine` class
- **Crawler scheduling**: [crawler.py](crawler.py) - `RSSCrawler.schedule_crawler()`
- **UI styling**: [templates/layout.html](templates/layout.html) - Bootstrap 5 + custom gradient CSS
- **API routes**: [app.py](app.py) - `@app.get()` / `@app.post()` decorators
- **Config template**: [config.yaml](config.yaml) - all tunable parameters

## Startup Verification Checklist

1. ✓ `pip install -r requirements.txt`
2. ✓ Update `config.yaml` with affiliate IDs
3. ✓ `python app.py` starts FastAPI + background crawler
4. ✓ Visit `http://localhost:8000` to confirm HTML rendering
5. ✓ Check database: `sqlite3 articles.db "SELECT COUNT(*) FROM articles;"`
6. ✓ Verify crawler ran: `SELECT * FROM crawler_logs ORDER BY executed_at DESC LIMIT 1;`

## Conventions & Gotchas

- **YAML indentation**: Must be 2 spaces (Python yaml.safe_load is strict)
- **Timezone**: Uses local system time; no explicit UTC handling
- **HTML escaping**: FastAPI auto-escapes strings; use `HTMLResponse` for raw HTML
- **Article URLs**: Must be unique (DB constraint); duplicates silently skipped
- **Crawler errors**: Logged to `crawler_logs.errors` field, not stderr
- **CSS framework**: Bootstrap 5.3 CDN; no build process needed

## Monthly Revenue Target Strategy

To reach ¥1M/month, this system pursues:

1. **Content velocity**: 1-hour crawler interval → fresh "速報" (breaking news) appeals
2. **Keyword saturation**: Config-driven keyword targeting for high-intent affiliate keywords ("Switch", "PS5", "予約開始")
3. **Scalability**: Spin up new instances with different `config.yaml` for anime/tech/esports genres
4. **Conversion optimization**: AdSense blocks + contextual affiliate links reduce friction

Example calc: 10K daily visits × 3% CTR (click-through) on affiliate links × 500 yen avg commission = ~¥150K/month per site. 6-7 sites = ¥1M+.
