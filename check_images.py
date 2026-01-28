import sqlite3

conn = sqlite3.connect('articles.db')
cursor = conn.cursor()

# 記事と画像URLを確認
cursor.execute('SELECT title, image_url FROM articles LIMIT 5')
articles = cursor.fetchall()

for title, image_url in articles:
    status = '✓ あり' if image_url else '✗ なし'
    print(f'{status}: {title[:50]}...')
    if image_url:
        print(f'  → {image_url[:80]}...')

# 画像ありの記事数をカウント
cursor.execute('SELECT COUNT(*) FROM articles WHERE image_url IS NOT NULL AND image_url != ""')
with_image = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM articles')
total = cursor.fetchone()[0]

print(f'\n合計：{with_image}/{total} 件に画像あり')
conn.close()
