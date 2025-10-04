# 透過 r.jina.ai 讀取並節流
import logging
import time

import requests


logger = logging.getLogger(__name__)


def fetch_readable(url, rpm=10):
    """取得可讀內容；呼叫方負責錯誤處理"""
    # 簡單的速率限制：每分鐘最多 rpm 次請求
    time.sleep(60.0 / max(1, rpm))
    
    try:
        jina_url = f"https://r.jina.ai/{url}"
        response = requests.get(jina_url, timeout=20)
        
        if response.status_code != 200:
            logger.warning("Jina Reader returned %s for %s", response.status_code, url)
            return ""
        
        return response.text
        
    except Exception as e:
        logger.exception("Error fetching %s via Jina", url)
        return ""
