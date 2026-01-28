import feedparser
import schedule
import time
import yaml
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import requests
from urllib.parse import urljoin
from models import Article, DatabaseManager
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RSSCrawler:
    def __init__(self, config_path: str = "config.yaml"):
        """RSSクローラーの初期化"""
        self.config = self._load_config(config_path)
        self.db = DatabaseManager(self.config['database']['path'])
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """設定ファイルを読み込む"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def fetch_feed(self, feed_url: str, timeout: int = 30) -> Optional[feedparser.FeedParserDict]:
        """RSSフィードを取得"""
        try:
            logger.info(f"Fetching feed: {feed_url}")
            response = self.session.get(feed_url, timeout=timeout)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
            return feed
        except requests.RequestException as e:
            logger.error(f"Failed to fetch feed {feed_url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error parsing feed {feed_url}: {str(e)}")
            return None

    def extract_image_url(self, entry: Any) -> Optional[str]:
        """フィードエントリから画像URLを抽出"""
        if hasattr(entry, 'media_content') and entry.media_content:
            return entry.media_content[0].get('url')

        if hasattr(entry, 'image') and entry.image:
            return entry.image.get('href')

        if hasattr(entry, 'link'):
            return None

        return None

    def get_entry_content(self, entry: Any) -> str:
        """フィードエントリから本文を抽出"""
        if hasattr(entry, 'summary'):
            return entry.summary[:500]
        elif hasattr(entry, 'description'):
            return entry.description[:500]
        else:
            return ""

    def crawl_feed(self, feed_url: str, source: str) -> tuple[int, int, Optional[str]]:
        """単一フィードをクロール"""
        fetched_count = 0
        saved_count = 0
        error_msg = None

        feed = self.fetch_feed(feed_url)
        if not feed:
            error_msg = "Failed to fetch feed"
            self.db.save_crawler_log(feed_url, source, fetched_count, saved_count, error_msg)
            return fetched_count, saved_count, error_msg

        max_articles = self.config['crawler']['max_articles']

        try:
            for entry in feed.entries[:max_articles]:
                fetched_count += 1

                title = entry.get('title', 'No Title')
                url = entry.get('link', '')
                content = self.get_entry_content(entry)
                image_url = self.extract_image_url(entry)

                if not url:
                    logger.warning(f"Skipping entry without URL: {title}")
                    continue

                try:
                    published_at = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_at = datetime(*entry.published_parsed[:6])

                    article = Article(
                        title=title,
                        content=content,
                        url=url,
                        source=source,
                        image_url=image_url,
                        published_at=published_at
                    )

                    article_id = self.db.save_article(article)
                    if article_id:
                        saved_count += 1
                        logger.info(f"Saved article: {title}")
                    else:
                        logger.debug(f"Article already exists: {title}")

                except Exception as e:
                    logger.error(f"Error saving article {title}: {str(e)}")
                    error_msg = str(e)

        except Exception as e:
            logger.error(f"Error processing feed entries: {str(e)}")
            error_msg = str(e)

        self.db.save_crawler_log(feed_url, source, fetched_count, saved_count, error_msg)
        logger.info(f"Feed {source}: Fetched {fetched_count}, Saved {saved_count}")

        return fetched_count, saved_count, error_msg

    def crawl_all_feeds(self):
        """すべてのRSSフィードをクロール"""
        logger.info("Starting full feed crawl...")
        total_fetched = 0
        total_saved = 0

        for feed_config in self.config['rss_feeds']:
            feed_url = feed_config['url']
            source = feed_config['source']

            fetched, saved, error = self.crawl_feed(feed_url, source)
            total_fetched += fetched
            total_saved += saved

        logger.info(f"Full crawl complete. Total fetched: {total_fetched}, Total saved: {total_saved}")

        # 古い記事をクリーンアップ
        cleanup_days = self.config['crawler'].get('cleanup_days', 30)
        self.db.cleanup_old_articles(cleanup_days)
        logger.info(f"Cleaned up articles older than {cleanup_days} days")

    def schedule_crawler(self):
        """クローラーをスケジュール"""
        interval = self.config['crawler']['interval_minutes']

        schedule.every(interval).minutes.do(self.crawl_all_feeds)

        logger.info(f"Crawler scheduled to run every {interval} minutes")

        while True:
            schedule.run_pending()
            time.sleep(60)

    def start_scheduler_background(self):
        """バックグラウンドでスケジューラーを開始"""
        thread = threading.Thread(target=self.schedule_crawler, daemon=True)
        thread.start()
        logger.info("Crawler scheduler started in background")
        return thread


def run_crawler_once():
    """クローラーを1回実行（CLI用）"""
    crawler = RSSCrawler()
    crawler.crawl_all_feeds()


if __name__ == "__main__":
    run_crawler_once()
