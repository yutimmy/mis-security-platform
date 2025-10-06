# 驗證 AI 內容更新功能
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import create_app
from app.models.db import db
from app.models.schema import News


def main():
    app = create_app()
    
    with app.app_context():
        # 統計資料
        total = News.query.count()
        with_ai = News.query.filter(
            News.ai_content.isnot(None),
            News.ai_content != ''
        ).count()
        without_ai = total - with_ai
        
        print("=" * 60)
        print("資料庫新聞統計")
        print("=" * 60)
        print(f"總新聞數: {total}")
        print(f"有 AI 內容: {with_ai}")
        print(f"無 AI 內容: {without_ai}")
        print()
        
        # 顯示沒有 AI 內容的新聞（前 10 筆）
        if without_ai > 0:
            print("=" * 60)
            print("沒有 AI 內容的新聞（前 10 筆）")
            print("=" * 60)
            no_ai_news = News.query.filter(
                (News.ai_content.is_(None)) | (News.ai_content == '')
            ).limit(10).all()
            
            for news in no_ai_news:
                print(f"ID: {news.id}")
                print(f"標題: {news.title[:60]}...")
                print(f"來源: {news.source}")
                print(f"連結: {news.link}")
                print(f"CVE: {news.cve_id or 'None'}")
                print("-" * 60)
            
            print()
            print(f"💡 提示：執行 RSS 爬蟲時，這些新聞將自動更新 AI 內容")
            print(f"   （前提是 Google GenAI API 配額充足）")
        else:
            print("✅ 所有新聞都有 AI 內容！")
        
        print()


if __name__ == "__main__":
    main()
