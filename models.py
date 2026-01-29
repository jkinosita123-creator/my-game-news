import sqlite3
import hashlib
from datetime import datetime
from typing import List, Optional, Dict, Any
import json

class Article:
    def __init__(
        self,
        title: str,
        content: str,
        url: str,
        source: str,
        image_url: Optional[str] = None,
        published_at: Optional[datetime] = None
    ):
        self.title = title
        self.content = content
        self.url = url
        self.source = source
        self.image_url = image_url
        self.published_at = published_at or datetime.now()
        self.hash_id = self._generate_hash()
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def _generate_hash(self) -> str:
        """重複チェック用のハッシュID生成"""
        content = f"{self.title}:{self.url}".encode('utf-8')
        return hashlib.md5(content).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'content': self.content,
            'url': self.url,
            'source': self.source,
            'image_url': self.image_url,
            'published_at': self.published_at.isoformat(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'hash_id': self.hash_id
        }


class DatabaseManager:
    def __init__(self, db_path: str = "./articles.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """データベーススキーマの初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 記事テーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                source TEXT NOT NULL,
                image_url TEXT,
                published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                views INTEGER DEFAULT 0,
                is_featured BOOLEAN DEFAULT 0
            )
        ''')

        # アフィリエイトリンク埋め込み履歴テーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS affiliate_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                keyword TEXT NOT NULL,
                link_type TEXT NOT NULL,
                original_url TEXT,
                affiliate_url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(article_id) REFERENCES articles(id) ON DELETE CASCADE
            )
        ''')

        # クローラー実行ログ
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crawler_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feed_url TEXT NOT NULL,
                source TEXT NOT NULL,
                articles_fetched INTEGER DEFAULT 0,
                articles_saved INTEGER DEFAULT 0,
                errors TEXT,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # インデックス作成
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hash_id ON articles(hash_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_published_at ON articles(published_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON articles(source)')

        conn.commit()
        conn.close()

    def article_exists(self, hash_id: str) -> bool:
        """重複チェック"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM articles WHERE hash_id = ?', (hash_id,))
        result = cursor.fetchone() is not None
        conn.close()
        return result

    def save_article(self, article: Article) -> Optional[int]:
        """記事をDBに保存"""
        if self.article_exists(article.hash_id):
            return None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO articles (
                    hash_id, title, content, url, source, image_url,
                    published_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article.hash_id,
                article.title,
                article.content,
                article.url,
                article.source,
                article.image_url,
                article.published_at.isoformat(),
                article.created_at.isoformat(),
                article.updated_at.isoformat()
            ))
            article_id = cursor.lastrowid
            conn.commit()
            return article_id
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()

    def get_recent_articles(
        self, limit: int = 50, offset: int = 0, source: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """最新記事を取得"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = 'SELECT * FROM articles'
        params = []

        if source:
            query += ' WHERE source = ?'
            params.append(source)

        query += ' ORDER BY published_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        articles = [dict(row) for row in rows]
        # published_at を datetime オブジェクトに変換
        for article in articles:
            if isinstance(article['published_at'], str):
                try:
                    article['published_at'] = datetime.fromisoformat(article['published_at'])
                except:
                    article['published_at'] = datetime.now()
        return articles

    def get_article_by_id(self, article_id: int) -> Optional[Dict[str, Any]]:
        """IDで記事を取得"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM articles WHERE id = ?', (article_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None
        
        article = dict(row)
        # published_at を datetime オブジェクトに変換
        if isinstance(article['published_at'], str):
            try:
                article['published_at'] = datetime.fromisoformat(article['published_at'])
            except:
                article['published_at'] = datetime.now()
        
        return article

    def increment_views(self, article_id: int):
        """閲覧数をインクリメント"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE articles SET views = views + 1 WHERE id = ?', (article_id,))
        conn.commit()
        conn.close()

    def save_affiliate_link(
        self, article_id: int, keyword: str, link_type: str,
        original_url: Optional[str], affiliate_url: str
    ):
        """アフィリエイトリンクを記録"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO affiliate_links (
                article_id, keyword, link_type, original_url, affiliate_url
            ) VALUES (?, ?, ?, ?, ?)
        ''', (article_id, keyword, link_type, original_url, affiliate_url))

        conn.commit()
        conn.close()

    def save_crawler_log(
        self, feed_url: str, source: str, fetched: int, saved: int,
        errors: Optional[str] = None
    ):
        """クローラーログを保存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO crawler_logs (
                feed_url, source, articles_fetched, articles_saved, errors
            ) VALUES (?, ?, ?, ?, ?)
        ''', (feed_url, source, fetched, saved, errors))

        conn.commit()
        conn.close()

    def get_total_articles(self) -> int:
        """総記事数を取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM articles')
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_articles_by_source(self) -> Dict[str, int]:
        """ソース別記事数を取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT source, COUNT(*) as count FROM articles GROUP BY source')
        results = cursor.fetchall()
        conn.close()
        return {row[0]: row[1] for row in results}

    def cleanup_old_articles(self, days: int = 30):
        """古い記事を削除"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM articles
            WHERE datetime(created_at) < datetime('now', ? || ' days')
        ''', (f'-{days}',))

        conn.commit()
        conn.close()

    def search_articles(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """全文検索"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        search_query = f"%{query}%"
        cursor.execute('''
            SELECT * FROM articles
            WHERE title LIKE ? OR content LIKE ?
            ORDER BY published_at DESC
            LIMIT ?
        ''', (search_query, search_query, limit))

        rows = cursor.fetchall()
        conn.close()

        articles = [dict(row) for row in rows]
        # published_at を datetime オブジェクトに変換
        for article in articles:
            if isinstance(article['published_at'], str):
                try:
                    article['published_at'] = datetime.fromisoformat(article['published_at'])
                except:
                    article['published_at'] = datetime.now()
        
        return articles
