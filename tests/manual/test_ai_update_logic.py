# 測試 AI 內容更新邏輯
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import create_app
from app.models.db import db
from app.models.schema import News


def test_update_logic():
    """測試更新邏輯（不實際執行 API 呼叫）"""
    app = create_app()
    
    with app.app_context():
        # 找一筆沒有 AI 內容的新聞
        news_without_ai = News.query.filter(
            (News.ai_content.is_(None)) | (News.ai_content == '')
        ).first()
        
        if not news_without_ai:
            print("❌ 資料庫中沒有缺少 AI 內容的新聞")
            return
        
        print("=" * 60)
        print("測試案例：模擬更新沒有 AI 內容的新聞")
        print("=" * 60)
        print(f"ID: {news_without_ai.id}")
        print(f"標題: {news_without_ai.title}")
        print(f"來源: {news_without_ai.source}")
        print(f"當前 AI 內容: {'無' if not news_without_ai.ai_content else '有'}")
        print(f"當前關鍵字: {news_without_ai.keyword or '無'}")
        print()
        
        # 模擬 AI 分析結果
        mock_ai_analysis = {
            "summary": "這是模擬的摘要",
            "translation": "This is a mock translation",
            "keywords": ["test", "mock", "ai"],
            "usage": "這是模擬的利用方式"
        }
        
        print("模擬 AI 分析結果:")
        print(f"  摘要: {mock_ai_analysis['summary']}")
        print(f"  關鍵字: {', '.join(mock_ai_analysis['keywords'])}")
        print()
        
        # 詢問是否執行測試更新
        response = input("是否執行測試更新？(y/n): ").strip().lower()
        
        if response == 'y':
            import json
            
            # 更新新聞
            news_without_ai.ai_content = json.dumps(mock_ai_analysis, ensure_ascii=False)
            news_without_ai.keyword = ', '.join(mock_ai_analysis['keywords'])
            
            try:
                db.session.commit()
                print("✅ 更新成功！")
                print()
                print("更新後狀態:")
                print(f"  AI 內容: {'有' if news_without_ai.ai_content else '無'}")
                print(f"  關鍵字: {news_without_ai.keyword}")
                print()
                print("💡 提示：實際執行時，系統會自動偵測並更新所有沒有 AI 內容的新聞")
            except Exception as e:
                db.session.rollback()
                print(f"❌ 更新失敗: {e}")
        else:
            print("❌ 取消測試")


if __name__ == "__main__":
    test_update_logic()
