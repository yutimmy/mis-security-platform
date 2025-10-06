# 透過 r.jina.ai 讀取並節流
import logging
import time

import requests
from requests.exceptions import Timeout, RequestException


logger = logging.getLogger(__name__)


def fetch_readable(url, rpm=10, max_retries=3, timeout=30):
    """
    取得可讀內容，支援重試機制
    
    Args:
        url: 目標網址
        rpm: 每分鐘請求限制
        max_retries: 最大重試次數
        timeout: 請求超時時間（秒）
    
    Returns:
        str: 清理後的內容，失敗返回空字串
    """
    # 簡單的速率限制：每分鐘最多 rpm 次請求
    time.sleep(60.0 / max(1, rpm))
    
    jina_url = f"https://r.jina.ai/{url}"
    
    for attempt in range(max_retries):
        try:
            # 使用較長的超時時間和重試策略
            response = requests.get(
                jina_url, 
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; SecurityNewsBot/1.0)',
                    'Accept': 'text/plain, */*'
                }
            )
            
            if response.status_code == 200:
                return response.text
            
            elif response.status_code == 429:
                # 速率限制，等待後重試
                wait_time = (attempt + 1) * 10
                logger.warning(
                    "Jina Reader rate limited for %s, waiting %ds before retry %d/%d",
                    url, wait_time, attempt + 1, max_retries
                )
                time.sleep(wait_time)
                continue
            
            elif response.status_code >= 500:
                # 伺服器錯誤，短暫等待後重試
                wait_time = (attempt + 1) * 5
                logger.warning(
                    "Jina Reader server error %s for %s, retry %d/%d after %ds",
                    response.status_code, url, attempt + 1, max_retries, wait_time
                )
                time.sleep(wait_time)
                continue
            
            else:
                # 其他錯誤（4xx），不重試
                logger.warning(
                    "Jina Reader returned %s for %s, not retrying",
                    response.status_code, url
                )
                return ""
        
        except Timeout:
            wait_time = (attempt + 1) * 5
            logger.warning(
                "Timeout fetching %s via Jina (attempt %d/%d), waiting %ds",
                url, attempt + 1, max_retries, wait_time
            )
            if attempt < max_retries - 1:
                time.sleep(wait_time)
            continue
        
        except RequestException as e:
            wait_time = (attempt + 1) * 5
            logger.warning(
                "Request error fetching %s via Jina: %s (attempt %d/%d)",
                url, str(e), attempt + 1, max_retries
            )
            if attempt < max_retries - 1:
                time.sleep(wait_time)
            continue
        
        except Exception as e:
            logger.exception(
                "Unexpected error fetching %s via Jina (attempt %d/%d)",
                url, attempt + 1, max_retries
            )
            if attempt < max_retries - 1:
                time.sleep((attempt + 1) * 5)
            continue
    
    # 所有重試都失敗
    logger.error("Failed to fetch %s via Jina after %d attempts", url, max_retries)
    return ""
