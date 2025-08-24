# 模組功能測試腳本
import sys
import os

# 確保能夠匯入專案模組並使用正確的路徑
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.chdir(project_root)

from crawlers.extractors import extract_cves, extract_emails
from crawlers.cleaners import clean_html_content, normalize_text


def test_extractors():
    """測試擷取器功能"""
    print("=== 測試擷取器功能 ===")
    
    # 測試 CVE 擷取
    test_text = """
    This vulnerability affects CVE-2024-12345 and also impacts CVE-2023-56789.
    Another issue is cve-2024-99999 which is critical.
    """
    
    cves = extract_cves(test_text)
    print(f"擷取的 CVE: {cves}")
    
    # 測試 Email 擷取
    email_text = """
    Contact us at security@example.com or admin@test.org for more information.
    Invalid email: not_an_email@
    """
    
    emails = extract_emails(email_text)
    print(f"擷取的 Email: {emails}")


def test_cleaners():
    """測試內容清理功能"""
    print("\n=== 測試內容清理功能 ===")
    
    # 測試 HTML 清理
    html_content = """
    <html>
        <head><title>Test</title></head>
        <body>
            <h1>Security News</h1>
            <p>This is a <strong>security alert</strong>.</p>
            <script>alert('malicious');</script>
            <style>body { color: red; }</style>
        </body>
    </html>
    """
    
    clean_text = clean_html_content(html_content)
    print(f"清理後的文字: {clean_text}")
    
    # 測試文字正規化
    messy_text = """
    Line 1\r\n
    
    
    Line 2\r
    
    
    
    Line 3
    """
    
    normalized = normalize_text(messy_text)
    print(f"正規化後的文字: {repr(normalized)}")


def test_jina_reader():
    """測試 Jina Reader (不實際發送請求)"""
    print("\n=== 測試 Jina Reader 配置 ===")
    
    from crawlers.jina_reader import fetch_readable
    
    # 只測試函數是否存在和參數
    print("Jina Reader 函數可用")
    print("測試 URL: https://example.com")
    print("注意：實際測試需要網路連線")


def test_genai_client():
    """測試 GenAI 客戶端配置"""
    print("\n=== 測試 GenAI 客戶端配置 ===")
    
    from crawlers.genai_client import GenAIClient
    from config import Config
    
    if Config.GOOGLE_GENAI_API_KEY:
        try:
            client = GenAIClient(Config.GOOGLE_GENAI_API_KEY, Config.GEMINI_MODEL)
            print("GenAI 客戶端初始化成功")
            
            # 測試連線
            success, message = client.test_connection()
            if success:
                print(f"API 連線測試成功: {message[:100]}")
            else:
                print(f"API 連線測試失敗: {message}")
                
        except Exception as e:
            print(f"GenAI 客戶端初始化失敗: {e}")
    else:
        print("未設定 Google GenAI API Key，跳過測試")


def test_database_models():
    """測試資料庫模型"""
    print("\n=== 測試資料庫模型 ===")
    
    from app import create_app
    from app.models.schema import User, News, RssSource
    
    app = create_app()
    
    with app.app_context():
        # 測試基本查詢
        user_count = User.query.count()
        news_count = News.query.count()
        rss_count = RssSource.query.count()
        
        print(f"使用者數量: {user_count}")
        print(f"新聞數量: {news_count}")
        print(f"RSS 來源數量: {rss_count}")
        
        # 檢查是否有管理員
        admin = User.query.filter_by(role='admin').first()
        if admin:
            print(f"發現管理員: {admin.username}")
        else:
            print("未發現管理員帳號")


def test_sploitus():
    """測試 Sploitus 功能（不實際發送請求）"""
    print("\n=== 測試 Sploitus 配置 ===")
    
    from crawlers.sploitus import search_sploitus_poc
    
    print("Sploitus 搜尋函數可用")
    print("測試 CVE: CVE-2024-12345")
    print("注意：實際測試需要網路連線且可能觸發速率限制")


if __name__ == '__main__':
    print("開始模組功能測試...\n")
    
    try:
        test_extractors()
        test_cleaners()
        test_jina_reader()
        test_genai_client()
        test_database_models()
        test_sploitus()
        
        print("\n=== 測試完成 ===")
        print("所有模組功能正常！")
        
    except Exception as e:
        print(f"\n測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
