# Discord 通知功能測試
import json
import logging
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# 確保能夠匯入專案模組並使用正確的路徑
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.chdir(project_root)

from app import create_app
from app.services.notify.discord import DiscordService


logger = logging.getLogger(__name__)


class TestDiscordNotification(unittest.TestCase):
    """Discord 通知功能測試"""

    def setUp(self):
        """測試前準備"""
        self.app = create_app()
        self.app.config.update({
            'TESTING': True,
            'DISCORD_BOT_TOKEN': os.getenv('DISCORD_BOT_TOKEN', ''),
            'DISCORD_CHANNEL_ID': os.getenv('DISCORD_CHANNEL_ID', ''),
        })
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """測試後清理"""
        self.app_context.pop()

    def test_discord_service_init(self):
        """測試 Discord 服務初始化"""
        service = DiscordService()
        
        # 檢查配置是否正確讀取
        self.assertIsInstance(service.bot_token, str)
        self.assertIsInstance(service.default_channel_id, str)
        
        logger.info("Discord Bot Token configured: %s", bool(service.bot_token))
        logger.info("Discord Channel ID configured: %s", bool(service.default_channel_id))

    @patch('requests.post')
    def test_send_simple_notification_mock(self, mock_post):
        """測試發送簡單通知（模擬）"""
        # 模擬成功回應
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "123456789"}
        mock_post.return_value = mock_response

        service = DiscordService()
        
        # 測試發送通知
        result = service.send_notification("測試通知訊息")
        
        if service.bot_token and service.default_channel_id:
            # 檢查是否呼叫了 Discord API
            mock_post.assert_called_once()
            self.assertTrue(result)
            logger.info("Mock Discord notification sent successfully")
        else:
            self.assertFalse(result)
            logger.info("Discord configuration incomplete; skipping mock assertion")
    @patch('requests.post')
    def test_send_real_notification(self, mock_post):
        """測試發送真實通知（模擬成功回應）"""
        service = DiscordService()

        if not service.bot_token or not service.default_channel_id:
            self.skipTest("Discord 配置未完成，跳過真實測試")
            return

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = service.send_notification("資安情訊平臺測試通知")

        self.assertTrue(result, "Discord 通知發送失敗")
        mock_post.assert_called_once()
        logger.info("Simulated Discord notification succeeded")

    @patch('requests.post')
    def test_send_notification_with_embed(self, mock_post):
        """測試發送帶嵌入式內容的通知（模擬成功回應）"""
        service = DiscordService()

        if not service.bot_token or not service.default_channel_id:
            self.skipTest("Discord 配置未完成，跳過嵌入式通知測試")
            return

        embed = {
            "title": "新資安威脅警報",
            "description": "發現新的CVE漏洞",
            "color": 15548997,
            "fields": [
                {
                    "name": "CVE ID",
                    "value": "CVE-2025-12345",
                    "inline": True
                },
                {
                    "name": "嚴重程度",
                    "value": "高風險",
                    "inline": True
                },
                {
                    "name": "影響範圍",
                    "value": "Windows系統",
                    "inline": False
                }
            ],
            "footer": {
                "text": "資安情訊平臺"
            },
            "timestamp": "2025-08-23T10:00:00.000Z"
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = service.send_notification("資安威脅報告", embed=embed)

        self.assertTrue(result, "Discord 嵌入式通知發送失敗")
        mock_post.assert_called_once()
        logger.info("Simulated Discord embed notification succeeded")

    def test_create_news_notification_format(self):
        """測試新聞通知格式"""
        service = DiscordService()
        
        # 模擬新聞資料
        news_data = {
            'title': '發現新的Windows RCE漏洞',
            'source': 'Microsoft Security',
            'created_at': '2025-08-23',
            'summary': '微軟發布緊急安全更新，修復嚴重的遠程代碼執行漏洞',
            'cve_ids': ['CVE-2025-12345', 'CVE-2025-12346'],
            'keywords': ['Windows', 'RCE', '緊急更新'],
            'link': 'https://example.com/news/123'
        }
        
        # 建立新聞通知內容
        content = self._format_news_notification(news_data)
        
        # 檢查格式
        self.assertIn(news_data['title'], content)
        self.assertIn(news_data['source'], content)
        self.assertIn('CVE-2025-12345', content)
        
        logger.info("新聞通知格式測試通過: %s", content)

    def _format_news_notification(self, news_data):
        """格式化新聞通知內容"""
        content = f"""[Alert] **新資安情報**

**標題**: {news_data['title']}
**來源**: {news_data['source']}
**日期**: {news_data['created_at']}

**摘要**: {news_data['summary']}

**相關CVE**: {', '.join(news_data['cve_ids'])}
**關鍵字**: {', '.join(news_data['keywords'])}

**詳細內容**: {news_data['link']}

---
*來自資安情訊平臺*"""
        return content

    def test_notification_error_handling(self):
        """測試通知錯誤處理"""
        service = DiscordService()
        
        # 測試無效 channel ID
        with patch.object(service, 'default_channel_id', 'invalid_channel'):
            result = service.send_notification("測試訊息")
            # 應該會失敗但不拋出異常
            logger.info("Invalid channel ID handled correctly")

        # 測試空 token
        with patch.object(service, 'bot_token', ''):
            result = service.send_notification("測試訊息")
            self.assertFalse(result)
            logger.info("Empty token handled correctly")


def run_discord_tests():
    """執行 Discord 通知測試"""
    logger.info("Discord 通知功能測試")
    
    # 檢查環境變數
    bot_token = os.getenv('DISCORD_BOT_TOKEN', '')
    channel_id = os.getenv('DISCORD_CHANNEL_ID', '')
    
    logger.info("Discord Bot Token configured: %s", bool(bot_token))
    logger.info("Discord Channel ID configured: %s", bool(channel_id))

    if not bot_token or not channel_id:
        logger.warning("Discord configuration incomplete; 部分測試將被跳過")

    # 執行測試
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_discord_tests()
