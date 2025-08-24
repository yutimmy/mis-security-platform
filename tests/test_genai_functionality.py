# Google GenAI 功能測試
import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock

# 確保能夠匯入專案模組並使用正確的路徑
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.chdir(project_root)

from config import Config
from crawlers.genai_client import GenAIClient


class TestGenAIFunctionality(unittest.TestCase):
    """Google GenAI 功能測試"""

    def setUp(self):
        """測試前準備"""
        self.api_key = os.getenv('GOOGLE_GENAI_API_KEY', '')
        self.model = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')

    def test_genai_client_init(self):
        """測試 GenAI 客戶端初始化"""
        if not self.api_key:
            self.skipTest("Google GenAI API Key 未設定，跳過初始化測試")
            return

        try:
            client = GenAIClient(api_key=self.api_key, model=self.model)
            self.assertIsNotNone(client.model)
            self.assertEqual(client.model_name, self.model)
            print("✓ GenAI 客戶端初始化成功")
            
        except Exception as e:
            self.fail(f"GenAI 客戶端初始化失敗: {e}")

    def test_genai_connection(self):
        """測試 GenAI 連線"""
        if not self.api_key:
            self.skipTest("Google GenAI API Key 未設定，跳過連線測試")
            return

        try:
            client = GenAIClient(api_key=self.api_key)
            success, response = client.test_connection()
            
            self.assertTrue(success, f"GenAI 連線測試失敗: {response}")
            self.assertIsInstance(response, str)
            self.assertGreater(len(response), 0)
            
            print("✓ GenAI 連線測試通過")
            print(f"API 回應: {response}")
            
        except Exception as e:
            self.fail(f"GenAI 連線測試失敗: {e}")

    def test_english_news_analysis(self):
        """測試英文新聞分析"""
        if not self.api_key:
            self.skipTest("Google GenAI API Key 未設定，跳過英文新聞分析測試")
            return

        # 模擬英文資安新聞
        sample_english_news = """
        A critical vulnerability has been discovered in Windows operating system that allows 
        remote code execution. The vulnerability, tracked as CVE-2025-12345, affects Windows 
        10 and Windows 11 systems. Attackers can exploit this vulnerability by sending specially 
        crafted network packets to vulnerable systems. Microsoft has released emergency security 
        updates to address this issue. Users are strongly advised to apply the patches immediately.
        """

        try:
            client = GenAIClient(api_key=self.api_key)
            result = client.generate_analysis(
                text=sample_english_news,
                news_title="Critical Windows RCE Vulnerability Discovered",
                source="Microsoft Security"
            )
            
            # 驗證回應結構
            self.assertIsInstance(result, dict)
            self.assertIn('summary', result)
            self.assertIn('translation', result)
            self.assertIn('how_to_exploit', result)
            self.assertIn('keywords', result)
            
            # 驗證內容品質
            self.assertGreater(len(result['summary']), 20)
            self.assertGreater(len(result['translation']), 20)
            self.assertGreater(len(result['how_to_exploit']), 50)
            self.assertIsInstance(result['keywords'], list)
            self.assertGreater(len(result['keywords']), 2)
            
            print("✓ 英文新聞分析測試通過")
            print(f"摘要: {result['summary']}")
            print(f"翻譯: {result['translation'][:100]}...")
            print(f"關鍵字: {result['keywords']}")
            
        except Exception as e:
            self.fail(f"英文新聞分析測試失敗: {e}")

    def test_chinese_news_analysis(self):
        """測試中文新聞分析"""
        if not self.api_key:
            self.skipTest("Google GenAI API Key 未設定，跳過中文新聞分析測試")
            return

        # 模擬中文資安新聞
        sample_chinese_news = """
        研究人員發現了一個影響 Apache Struts 框架的嚴重安全漏洞，編號為 CVE-2025-54321。
        該漏洞允許攻擊者透過精心構造的 HTTP 請求來執行任意代碼。受影響的版本包括 
        Struts 2.5.x 到 2.7.x 系列。攻擊者可利用此漏洞完全控制受影響的 Web 應用程式。
        Apache 安全團隊已發布修補程式，建議所有使用者立即更新到最新版本。
        此漏洞的CVSS評分為9.8分，屬於嚴重等級。
        """

        try:
            client = GenAIClient(api_key=self.api_key)
            result = client.generate_analysis(
                text=sample_chinese_news,
                news_title="Apache Struts 嚴重漏洞被發現",
                source="安全研究團隊"
            )
            
            # 驗證回應結構
            self.assertIsInstance(result, dict)
            self.assertIn('summary', result)
            self.assertIn('translation', result)
            self.assertIn('how_to_exploit', result)
            self.assertIn('keywords', result)
            
            # 驗證內容品質
            self.assertGreater(len(result['summary']), 20)
            self.assertGreater(len(result['translation']), 20)
            self.assertGreater(len(result['how_to_exploit']), 50)
            self.assertIsInstance(result['keywords'], list)
            self.assertGreater(len(result['keywords']), 2)
            
            print("✓ 中文新聞分析測試通過")
            print(f"摘要: {result['summary']}")
            print(f"翻譯: {result['translation'][:100]}...")
            print(f"關鍵字: {result['keywords']}")
            
        except Exception as e:
            self.fail(f"中文新聞分析測試失敗: {e}")

    def test_genai_response_format(self):
        """測試 GenAI 回應格式處理"""
        if not self.api_key:
            self.skipTest("Google GenAI API Key 未設定，跳過格式測試")
            return

        # 測試簡短文本
        short_text = "This is a test security alert about CVE-2025-99999."
        
        try:
            client = GenAIClient(api_key=self.api_key)
            result = client.generate_analysis(
                text=short_text,
                news_title="Test Alert",
                source="Test Source"
            )
            
            # 驗證 JSON 結構完整性
            required_keys = ['summary', 'translation', 'how_to_exploit', 'keywords']
            for key in required_keys:
                self.assertIn(key, result, f"缺少必要欄位: {key}")
            
            # 驗證 keywords 是陣列
            self.assertIsInstance(result['keywords'], list)
            
            print("✓ GenAI 回應格式測試通過")
            print(f"回應結構: {list(result.keys())}")
            
        except Exception as e:
            self.fail(f"GenAI 回應格式測試失敗: {e}")

    def test_genai_error_handling(self):
        """測試 GenAI 錯誤處理"""
        # 測試無效 API Key
        try:
            client = GenAIClient(api_key="invalid_key")
            result = client.generate_analysis("test text")
            
            # 即使 API Key 無效，也應該返回預設結構
            self.assertIsInstance(result, dict)
            self.assertIn('summary', result)
            
            print("✓ 無效 API Key 錯誤處理正常")
            
        except ValueError as e:
            # 如果在初始化時就檢查 API Key，這也是正確的
            print("✓ API Key 驗證正常")

    def test_genai_performance(self):
        """測試 GenAI 性能"""
        if not self.api_key:
            self.skipTest("Google GenAI API Key 未設定，跳過性能測試")
            return

        import time
        
        # 測試文本
        test_text = "A new vulnerability CVE-2025-11111 affects multiple systems."
        
        try:
            client = GenAIClient(api_key=self.api_key)
            
            start_time = time.time()
            result = client.generate_analysis(test_text)
            end_time = time.time()
            
            duration = end_time - start_time
            
            # 檢查回應時間（應該在合理範圍內）
            self.assertLess(duration, 30, "GenAI 回應時間過長")
            
            print(f"✓ GenAI 性能測試通過 (回應時間: {duration:.2f}秒)")
            
        except Exception as e:
            self.fail(f"GenAI 性能測試失敗: {e}")

    @patch('google.generativeai.GenerativeModel')
    def test_genai_mock_response(self, mock_model):
        """測試 GenAI 模擬回應"""
        # 設定模擬回應
        mock_response = MagicMock()
        mock_response.text = """
        {
            "summary": "測試摘要",
            "translation": "Test translation",
            "how_to_exploit": "測試利用方式說明",
            "keywords": ["測試", "關鍵字"]
        }
        """
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        # 測試
        client = GenAIClient(api_key="test_key")
        result = client.generate_analysis("test text")
        
        self.assertEqual(result['summary'], "測試摘要")
        self.assertEqual(result['translation'], "Test translation")
        self.assertIn("測試", result['keywords'])
        
        print("✓ GenAI 模擬回應測試通過")

    def test_json_extraction(self):
        """測試 JSON 提取功能"""
        # 模擬 AI 回應帶有額外文字
        messy_response = """
        以下是分析結果：
        
        {
            "summary": "這是摘要",
            "translation": "This is translation",
            "how_to_exploit": "利用方式說明",
            "keywords": ["關鍵字1", "關鍵字2"]
        }
        
        希望這個分析對您有幫助。
        """
        
        # 測試 JSON 提取
        json_start = messy_response.find('{')
        json_end = messy_response.rfind('}') + 1
        
        self.assertGreater(json_start, 0)
        self.assertGreater(json_end, json_start)
        
        json_str = messy_response[json_start:json_end]
        result = json.loads(json_str)
        
        self.assertIn('summary', result)
        self.assertIn('keywords', result)
        
        print("✓ JSON 提取功能測試通過")


def run_genai_tests():
    """執行 GenAI 功能測試"""
    print("=" * 50)
    print("🤖 Google GenAI 功能測試")
    print("=" * 50)
    
    # 檢查環境變數
    api_key = os.getenv('GOOGLE_GENAI_API_KEY', '')
    model = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
    
    print(f"Google GenAI API Key: {'✓ 已設定' if api_key else '✗ 未設定'}")
    print(f"Gemini Model: {model}")
    print()
    
    if not api_key:
        print("⚠️  警告：Google GenAI API Key 未設定，部分測試將被跳過")
        print("請在 .env 檔案中設定 GOOGLE_GENAI_API_KEY")
        print()
    
    # 執行測試
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_genai_tests()
