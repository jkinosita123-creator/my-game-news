from models import DatabaseManager

db = DatabaseManager()
count = db.get_total_articles()
print(f'記事数: {count}')

if count > 0:
    articles = db.get_recent_articles(limit=1)
    if articles:
        article = articles[0]
        print(f'ID: {article["id"]}')
        print(f'タイトル: {article["title"]}')
        print(f'published_at型: {type(article["published_at"])}')
        print(f'published_at値: {article["published_at"]}')
