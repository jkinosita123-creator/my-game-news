# ゲーム特化アフィリエイトサイト生成システム 🚀

超速報を武器にアクセスを稼ぎ、広告とアフィリエイトで月100万円の収益を目指すPythonシステムです。

`config.yaml` を書き換えるだけで、別のゲームジャンルサイトを量産できる「艦隊運営」仕様になっています。

## 🎯 システムの特徴

- **自動クローラー**: RSSフィードから1時間おきに最新ニュースを全自動取得・DB保存
- **ハイブリッド収益**: Google AdSense + Amazon/楽天アフィリエイトリンクの自動埋め込み
- **高速表示**: FastAPIによる超高速なサイト表示
- **美しいデザイン**: Bootstrap 5を使用したレスポンシブマガジンデザイン
- **無限スケーラビリティ**: config.yaml を変更するだけで新規サイト量産可能

## 📁 ファイル構成

```
GameNewsProject/
├── app.py                 # FastAPI サーバー（サイト表示）
├── crawler.py            # RSSクローラー（記事自動取得）
├── models.py             # SQLiteデータベース設計
├── config.yaml           # サイト設定ファイル
├── requirements.txt      # Python依存パッケージ一覧
├── README.md             # このファイル
└── templates/
    ├── layout.html       # 基本テンプレート
    └── index.html        # インデックスページ
```

## 🚀 起動手順（1分で起動できます）

### 1. 環境構築

```bash
# Python環境がインストールされていることを確認
python --version

# 依存パッケージのインストール
pip install -r requirements.txt
```

### 2. 設定カスタマイズ

`config.yaml` を編集して、あなたのサイト設定を入力します：

```yaml
site:
  name: "あなたのサイト名"
  description: "サイトの説明"

affiliate:
  amazon:
    tracking_id: "YOUR_AMAZON_TRACKING_ID"  # Amazonアソシエイトから取得
  rakuten:
    affiliate_id: "YOUR_RAKUTEN_AFFILIATE_ID"  # 楽天アフィリエイトから取得
  google_adsense:
    publisher_id: "YOUR_GOOGLE_ADSENSE_ID"  # Google AdSenseから取得
```

### 3. サーバー起動

```bash
# FastAPIサーバーを起動（クローラーは自動でバックグラウンド実行）
python app.py
```

または

```bash
# Uvicornで直接起動
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. ブラウザでアクセス

```
http://localhost:8000
```

## 🛠️ 追加コマンド

### クローラーを手動実行

```bash
python crawler.py
```

### APIエンドポイント

```bash
# 最新記事一覧を取得
curl http://localhost:8000/api/articles

# 統計情報を取得
curl http://localhost:8000/api/stats

# クローラーを手動実行
curl -X POST http://localhost:8000/api/crawl
```

## ⚙️ 詳細設定ガイド

### RSSフィードの追加

`config.yaml` の `rss_feeds` セクションに新しいフィードを追加：

```yaml
rss_feeds:
  - url: "https://example.com/feed.xml"
    source: "ソース名"
    priority: 1
```

### アフィリエイトキーワードの追加

新しいキーワードターゲットを追加：

```yaml
keywords:
  affiliate_targets:
    - keyword: "あなたのキーワード"
      product_type: "category"
      affiliate_links:
        - type: "amazon"
          url_pattern: "https://www.amazon.co.jp/s?k=キーワード"
```

### クローラー実行間隔の変更

```yaml
crawler:
  interval_minutes: 60  # デフォルト60分。変更可能
  timeout_seconds: 30
  max_articles: 500
  cleanup_days: 30  # 30日以上前の記事は自動削除
```

## 💰 収益化の仕組み

### 1. Google AdSense
- サイト全体に自動的に広告を表示
- `publisher_id` と `ad_slot` を設定するだけ

### 2. Amazon アフィリエイト
- 記事内の「Switch」「PS5」などのキーワードを自動検出
- Amazon商品ページへのアフィリエイトリンクに自動変換
- トラッキングID経由の成約で報酬獲得

### 3. 楽天アフィリエイト
- 同様にキーワード検出で楽天商品ページにリダイレクト
- アフィリエイトIDで報酬を追跡

## 🎓 高度な使い方

### 複数サイトの同時運営（艦隊運営）

```bash
# 異なる config.yaml を使い分けることで複数サイト運営可能
python app.py --config config-game.yaml
python app.py --config config-anime.yaml
python app.py --config config-tech.yaml
```

### データベースの確認

SQLiteデータベースを確認：

```bash
sqlite3 articles.db
sqlite> SELECT COUNT(*) FROM articles;
sqlite> SELECT title, source, published_at FROM articles LIMIT 10;
sqlite> .exit
```

### ログの確認

```bash
# アプリケーションログ
tail -f logs/app.log
```

## 📊 パフォーマンス最適化

- **キャッシング**: 記事は SQLite に保存され、高速アクセス可能
- **インデックス**: published_at、source、hash_id にインデックス設定
- **ワーカープロセス**: 複数ワーカーで並列処理
- **非同期クローリング**: バックグラウンドで自動実行

## 🔒 セキュリティ注意事項

1. **アフィリエイトIDの管理**
   - `config.yaml` には本番環境ではシークレット情報を記載しないでください
   - 環境変数から読み込むようにカスタマイズしてください

2. **データベースバックアップ**
   - `articles.db` は定期的にバックアップしてください

3. **HTTPS設定**
   - 本番環境では HTTPS を必ず有効にしてください

## 📈 月100万円達成のコツ

1. **トレンドキーワード**: 予約開始などの速報性の高いニュースを優先
2. **記事数**: 1日最低50記事以上の更新を目指す
3. **SEO最適化**: タイトルと本文に検索キーワードを自然に含める
4. **アフィリエイト配置**: キーワードマッチングの精度を上げる
5. **複数ジャンル**: 3～5個の異なるジャンルサイトで相乗効果

## 🐛 トラブルシューティング

### クローラーが動作しない

```bash
# ログを確認
python crawler.py  # 直接実行してエラーを確認

# RSSフィードURLが有効か確認
curl https://example.com/feed.xml
```

### サイトが表示されない

```bash
# ポート確認（8000が使用中の場合）
netstat -ano | findstr :8000

# ポートを変更
python app.py --port 8001
```

### アフィリエイトリンクが表示されない

- `config.yaml` でアフィリエイトID が正しく設定されているか確認
- キーワードが記事に含まれているか確認

## 📞 サポート

問題が発生した場合：

1. ログを確認: `logs/app.log`
2. データベースをリセット: `rm articles.db` で再作成
3. 設定ファイルを再確認: `config.yaml` の構文チェック

## 📜 ライセンス

MIT License - 自由に改変・配布可能です

---

**準備ができました！上記のコマンドで今すぐ起動できます。** 🚀

`python app.py` を実行してから `http://localhost:8000` にアクセスしてください！
