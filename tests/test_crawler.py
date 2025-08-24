# 資安情訊平台 - 完整測試套件
import sys
import os
import requests
import json
import unittest
from datetime import datetime, timedelta

# 確保能夠匯入專案模組並使用正確的路徑
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.chdir(project_root)

from app import create_app
from app.models.db import db
from app.models.schema import News, RssSource, User, CvePoc, JobRun
from app.services.rss_service import RSSService
from app.services.poc_service import POCService
from app.services.ai_service import AIService
from crawlers.rss import process_rss_feed, save_items_to_db
from crawlers.genai_client import GenAIClient
from config import Config


class TestCrawlerSystem(unittest.TestCase):
    """爬蟲系統測試類別"""
    
    @classmethod
    def setUpClass(cls):
        """測試類別初始化"""
        cls.app = create_app()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        
    @classmethod
    def tearDownClass(cls):
        """測試類別清理"""
        cls.app_context.pop()
    
    def test_database_connection(self):
        """測試資料庫連接"""
        print("\n1. 📊 測試資料庫連接...")
        try:
            news_count = News.query.count()
            user_count = User.query.count()
            rss_count = RssSource.query.count()
            
            print(f"   ✅ 資料庫連接正常")
            print(f"   📰 新聞數量: {news_count}")
            print(f"   👥 用戶數量: {user_count}")
            print(f"   📡 RSS來源: {rss_count}")
            
            self.assertTrue(True)  # 如果能執行到這裡就表示成功
        except Exception as e:
            print(f"   ❌ 資料庫連接失敗: {e}")
            self.fail(f"資料庫連接失敗: {e}")
    
    def test_rss_service(self):
        """測試 RSS 服務"""
        print("\n2. 📡 測試 RSS 服務...")
        try:
            rss_service = RSSService()
            print("   ✅ RSS 服務初始化成功")
            
            if rss_service.genai_client:
                print("   ✅ GenAI 客戶端可用")
                
                # 測試 GenAI 連接
                success, message = rss_service.genai_client.test_connection()
                if success:
                    print(f"   ✅ GenAI 連接測試成功: {message}")
                else:
                    print(f"   ⚠️  GenAI 連接測試失敗: {message}")
            else:
                print("   ⚠️  GenAI 客戶端未可用")
                
            self.assertIsInstance(rss_service, RSSService)
        except Exception as e:
            print(f"   ❌ RSS 服務測試失敗: {e}")
            self.fail(f"RSS 服務測試失敗: {e}")
    
    def test_poc_service(self):
        """測試 POC 服務"""
        print("\n3. 🔍 測試 POC 服務...")
        try:
            poc_service = POCService()
            print("   ✅ POC 服務初始化成功")
            
            self.assertIsInstance(poc_service, POCService)
        except Exception as e:
            print(f"   ❌ POC 服務測試失敗: {e}")
            self.fail(f"POC 服務測試失敗: {e}")
    
    def test_ai_service(self):
        """測試 AI 服務"""
        print("\n4. 🤖 測試 AI 服務...")
        try:
            ai_service = AIService()
            if ai_service.genai_client:
                test_result = ai_service.genai_client.test_connection()
                if test_result[0]:
                    print("   ✅ AI 服務可用")
                else:
                    print(f"   ❌ AI 連接失敗: {test_result[1]}")
            else:
                print("   ⚠️  AI 客戶端未配置")
                
            self.assertIsInstance(ai_service, AIService)
        except Exception as e:
            print(f"   ❌ AI 服務測試失敗: {e}")
            self.fail(f"AI 服務測試失敗: {e}")
    
    def test_news_with_cve(self):
        """測試CVE新聞數據"""
        print("\n5. 📰 檢查測試數據...")
        try:
            cve_news = News.query.filter(News.cve_id.isnot(None)).first()
            if cve_news:
                print(f"   ✅ 找到含CVE的新聞: {cve_news.title[:50]}...")
                print(f"   🔢 CVE: {cve_news.cve_id}")
                self.assertIsNotNone(cve_news.cve_id)
            else:
                print("   ⚠️  沒有找到含CVE的新聞")
        except Exception as e:
            print(f"   ❌ 新聞查詢失敗: {e}")
            self.fail(f"新聞查詢失敗: {e}")


def test_rss_crawl():
    """測試 RSS 爬蟲功能（獨立函數）"""
    app = create_app()
    
    with app.app_context():
        print("\n📡 開始測試 RSS 爬蟲...")
        
        # 取得啟用的 RSS 來源
        rss_sources = RssSource.query.filter_by(enabled=True).all()
        
        if not rss_sources:
            print("   ❌ 沒有找到啟用的 RSS 來源")
            return
        
        # 初始化 GenAI 客戶端（如果有 API key）
        genai_client = None
        if Config.GOOGLE_GENAI_API_KEY:
            try:
                genai_client = GenAIClient()
                print("   ✅ GenAI 客戶端初始化成功")
            except Exception as e:
                print(f"   ⚠️  GenAI 客戶端初始化失敗：{e}")
        else:
            print("   ⚠️  未設定 Google GenAI API Key，跳過 AI 分析")
        
        total_stats = {
            'processed': 0,
            'new_items': 0,
            'errors': 0,
            'inserted': 0,
            'skipped': 0
        }
        
        # 處理每個 RSS 來源（只取第一個作為測試）
        for rss_source in rss_sources[:1]:  # 只處理第一個來源
            print(f"\n   處理 RSS 來源：{rss_source.name}")
            
            # 處理 RSS feed
            result = process_rss_feed(
                rss_source.link,
                rss_source.source,
                genai_client=genai_client,
                jina_rpm=Config.JINA_MAX_RPM
            )
            
            total_stats['processed'] += result['processed']
            total_stats['new_items'] += result['new_items']
            total_stats['errors'] += result['errors']
            
            if result['items']:
                # 儲存到資料庫
                save_stats = save_items_to_db(result['items'], db.session, News)
                total_stats['inserted'] += save_stats['inserted']
                total_stats['skipped'] += save_stats['skipped']
                total_stats['errors'] += save_stats['errors']
        
        print(f"\n   === RSS 爬蟲測試完成 ===")
        print(f"   總處理項目：{total_stats['processed']}")
        print(f"   新項目：{total_stats['new_items']}")
        print(f"   成功插入：{total_stats['inserted']}")
        print(f"   跳過（重複）：{total_stats['skipped']}")
        print(f"   錯誤：{total_stats['errors']}")


def test_api_endpoints():
    """測試API端點"""
    print("\n🌐 測試API端點...")
    base_url = "http://127.0.0.1:5000"
    
    try:
        # 測試健康檢查
        response = requests.get(f"{base_url}/api/healthz", timeout=5)
        if response.status_code == 200:
            print("   ✅ API健康檢查正常")
        else:
            print(f"   ❌ API健康檢查失敗: {response.status_code}")
        
        # 測試新聞API
        response = requests.get(f"{base_url}/api/news", timeout=5)
        if response.status_code == 200:
            data = response.json()
            news_count = len(data.get('data', {}).get('news', []))
            print(f"   ✅ 新聞API正常 (共{news_count}則新聞)")
        else:
            print(f"   ❌ 新聞API失敗: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("   ⚠️  無法連接到Flask服務器，請確保服務器正在運行")
    except Exception as e:
        print(f"   ❌ API測試失敗: {e}")


def add_sample_news():
    """添加示例新聞數據用於測試"""
    app = create_app()
    
    with app.app_context():
        print("\n📰 檢查並添加示例新聞數據...")
        
        # 檢查是否已有新聞
        existing_news = News.query.count()
        print(f"   現有新聞數量：{existing_news}")
        
        if existing_news < 5:  # 如果新聞數量少於5則添加示例數據
            sample_news = [
                {
                    "title": "Chrome 瀏覽器發現嚴重零日漏洞 CVE-2024-12345",
                    "link": "https://example.com/chrome-zero-day-1",
                    "source": "test",
                    "content": "Google Chrome 瀏覽器被發現存在一個嚴重的零日漏洞 CVE-2024-12345，攻擊者可利用此漏洞進行遠端程式碼執行。此漏洞影響所有 Chrome 版本，建議用戶立即更新至最新版本。研究人員指出，此漏洞可能被用於針對性攻擊，特別是對企業和政府機構的攻擊。",
                    "cve_id": "CVE-2024-12345",
                    "email": "security@google.com"
                },
                {
                    "title": "Linux Kernel 特權提升漏洞影響數百萬系統",
                    "link": "https://example.com/linux-privilege-escalation-2",
                    "source": "test",
                    "content": "Linux 核心被發現存在特權提升漏洞 CVE-2024-54321，影響所有主要 Linux 發行版。攻擊者可利用此漏洞獲得 root 權限，進行系統完全控制。各大 Linux 發行版已釋出安全更新，系統管理員應立即應用修補程式。此漏洞的 CVSS 評分為 8.8，屬於高危漏洞。",
                    "cve_id": "CVE-2024-54321",
                    "email": "security@kernel.org"
                },
                {
                    "title": "新型勒索軟體 'CryptoLock' 攻擊全球企業",
                    "link": "https://example.com/cryptolock-ransomware-3",
                    "source": "test",
                    "content": "一種名為 'CryptoLock' 的新型勒索軟體正在全球範圍內攻擊企業網路。該勒索軟體利用多種漏洞進行橫向移動，包括 CVE-2024-11111 和 CVE-2024-22222。受害企業的重要資料被加密，攻擊者要求高額贖金。資安專家建議企業加強端點防護並定期備份重要資料。",
                    "cve_id": "CVE-2024-11111, CVE-2024-22222",
                    "email": "incident@cert.org"
                }
            ]
            
            for i, news_data in enumerate(sample_news):
                # 檢查是否已存在
                existing = News.query.filter_by(link=news_data["link"]).first()
                if not existing:
                    news = News(
                        title=news_data["title"],
                        link=news_data["link"],
                        source=news_data["source"],
                        content=news_data["content"],
                        cve_id=news_data["cve_id"],
                        email=news_data["email"],
                        created_at=datetime.now() - timedelta(days=i)
                    )
                    db.session.add(news)
                    print(f"   ✅ 已添加示例新聞：{news_data['title'][:50]}...")
            
            try:
                db.session.commit()
                print("   ✅ 示例新聞添加完成！")
            except Exception as e:
                print(f"   ❌ 示例新聞添加失敗：{e}")
                db.session.rollback()
        else:
            print("   ✅ 已有足夠的新聞數據，跳過添加示例數據")


def run_all_tests():
    """執行所有測試"""
    print("🔍 開始完整功能測試...")
    print("=" * 60)
    
    # 1. 添加示例數據
    add_sample_news()
    
    # 2. 執行單元測試
    print("\n🧪 執行單元測試...")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCrawlerSystem)
    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(suite)
    
    # 3. 測試RSS爬蟲
    test_rss_crawl()
    
    # 4. 測試API端點
    test_api_endpoints()
    
    print("\n" + "=" * 60)
    print("🎉 完整功能測試完成！")
    print("\n💡 手動測試建議：")
    print("1. 開啟瀏覽器訪問 http://127.0.0.1:5000")
    print("2. 使用 admin / mis116isgood 登入管理後台")
    print("3. 在管理後台點擊「執行 RSS 爬蟲」測試按鈕")
    print("4. 在新聞列表頁面測試「查 POC」按鈕")
    print("5. 檢查統計頁面是否正常顯示")


if __name__ == '__main__':
    # 可以選擇運行特定測試或所有測試
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'unittest':
            # 只運行單元測試
            suite = unittest.TestLoader().loadTestsFromTestCase(TestCrawlerSystem)
            runner = unittest.TextTestRunner(verbosity=2)
            runner.run(suite)
        elif sys.argv[1] == 'rss':
            # 只運行RSS測試
            app = create_app()
            with app.app_context():
                test_rss_crawl()
        elif sys.argv[1] == 'api':
            # 只運行API測試
            test_api_endpoints()
        elif sys.argv[1] == 'sample':
            # 只添加示例數據
            add_sample_news()
    else:
        # 運行所有測試
        run_all_tests()
