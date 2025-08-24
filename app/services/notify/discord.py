# Discord 通知服務
import json
import requests
from datetime import datetime, timezone
from flask import current_app

from ...models.db import db
from ...models.schema import Notification


class DiscordService:
    """Discord 通知服務"""

    def __init__(self):
        self.bot_token = current_app.config.get('DISCORD_BOT_TOKEN', '')
        self.default_channel_id = current_app.config.get('DISCORD_CHANNEL_ID', '')

    def send_notification(self, content, channel_id=None, embed=None):
        """發送 Discord 通知"""
        if not self.bot_token:
            current_app.logger.warning("Discord bot token not configured")
            return False

        target_channel = channel_id or self.default_channel_id
        if not target_channel:
            current_app.logger.warning("Discord channel ID not configured")
            return False

        try:
            url = f"https://discord.com/api/v10/channels/{target_channel}/messages"
            headers = {
                "Authorization": f"Bot {self.bot_token}",
                "Content-Type": "application/json"
            }

            payload = {"content": content}
            if embed:
                payload["embeds"] = [embed]

            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                # 記錄通知
                self._log_notification(
                    notification_type='discord',
                    content=content,
                    status='sent'
                )
                return True
            else:
                current_app.logger.error(f"Discord API error: {response.status_code} - {response.text}")
                self._log_notification(
                    notification_type='discord',
                    content=content,
                    status='failed'
                )
                return False

        except Exception as e:
            current_app.logger.error(f"Discord notification failed: {str(e)}")
            self._log_notification(
                notification_type='discord',
                content=content,
                status='error'
            )
            return False

    def send_news_alert(self, news_item, channel_id=None):
        """發送新聞警報"""
        embed = {
            "title": news_item.title[:256],  # Discord 限制
            "description": (news_item.summary or news_item.content)[:2048],
            "url": news_item.url,
            "color": 0xff6b6b,  # 紅色
            "fields": [
                {
                    "name": "來源",
                    "value": news_item.rss_source.name if news_item.rss_source else "未知",
                    "inline": True
                },
                {
                    "name": "發布日期",
                    "value": news_item.published_at.strftime('%Y-%m-%d') if news_item.published_at else "未知",
                    "inline": True
                }
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # 如果有 CVE，加入欄位
        if hasattr(news_item, 'cve_list') and news_item.cve_list:
            cve_text = ", ".join(news_item.cve_list[:10])  # 最多顯示 10 個
            embed["fields"].append({
                "name": "CVE",
                "value": cve_text,
                "inline": False
            })

        content = f"🚨 **新資安情報** - {news_item.title}"
        return self.send_notification(content, channel_id, embed)

    def send_cve_alert(self, cve_id, poc_links=None, channel_id=None):
        """發送 CVE 警報"""
        embed = {
            "title": f"CVE 更新: {cve_id}",
            "description": f"POC 查詢完成",
            "color": 0xffa500,  # 橙色
            "fields": [
                {
                    "name": "CVE ID",
                    "value": cve_id,
                    "inline": True
                },
                {
                    "name": "更新時間",
                    "value": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
                    "inline": True
                }
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if poc_links and len(poc_links) > 0:
            embed["fields"].append({
                "name": "發現 POC",
                "value": f"找到 {len(poc_links)} 個相關 POC",
                "inline": False
            })
            
            # 顯示前幾個 POC 連結
            poc_text = "\n".join(poc_links[:3])
            if len(poc_links) > 3:
                poc_text += f"\n... 及其他 {len(poc_links) - 3} 個"
            
            embed["fields"].append({
                "name": "POC 連結",
                "value": poc_text,
                "inline": False
            })
        else:
            embed["fields"].append({
                "name": "POC 狀態",
                "value": "未找到相關 POC",
                "inline": False
            })

        content = f"🔍 **CVE 分析完成** - {cve_id}"
        return self.send_notification(content, channel_id, embed)

    def send_job_status(self, job_type, status, details=None, channel_id=None):
        """發送任務狀態通知"""
        status_colors = {
            'success': 0x00ff00,  # 綠色
            'failed': 0xff0000,   # 紅色
            'running': 0xffff00   # 黃色
        }

        status_text = {
            'success': '✅ 成功',
            'failed': '❌ 失敗',
            'running': '⏳ 執行中'
        }

        embed = {
            "title": f"任務狀態更新 - {job_type}",
            "description": f"任務狀態: {status_text.get(status, status)}",
            "color": status_colors.get(status, 0x808080),
            "fields": [
                {
                    "name": "任務類型",
                    "value": job_type,
                    "inline": True
                },
                {
                    "name": "狀態",
                    "value": status_text.get(status, status),
                    "inline": True
                }
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if details:
            embed["fields"].append({
                "name": "詳細資訊",
                "value": str(details),
                "inline": False
            })

        content = f"📊 **任務更新** - {job_type}"
        return self.send_notification(content, channel_id, embed)

    def _log_notification(self, notification_type, content, status):
        """記錄通知到資料庫"""
        try:
            notification = Notification(
                type=notification_type,
                payload=content,
                target_role='all',
                status=status,
                sent_at=datetime.now(timezone.utc).date() if status == 'sent' else None
            )
            db.session.add(notification)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Failed to log notification: {e}")
            db.session.rollback()
