# 手動 POC 查詢（輸入 CVE → 回傳 POC 連結）
import logging
import re
import time

import requests
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


def search_sploitus_poc(cve_id, max_links=3):
    """
    在 Sploitus 搜尋指定 CVE 的 POC
    
    Args:
        cve_id: CVE 編號，如 "CVE-2024-12345"
        max_links: 最多返回幾個連結
        
    Returns:
        list: POC 連結清單
    """
    if not cve_id or not cve_id.startswith('CVE-'):
        logger.warning("Invalid CVE format: %s", cve_id)
        return []
    
    try:
        # 簡單的速率限制
        time.sleep(2)
        
        logger.info("Searching Sploitus for %s", cve_id)
        
        # 使用舊的搜尋方式 - 直接訪問帶有 query 參數的頁面
        search_query = cve_id.upper()
        search_url = f"https://sploitus.com/?query={search_query}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # 使用 session 以支持 cookies
        session = requests.Session()
        response = session.get(search_url, headers=headers, timeout=20)
        
        logger.debug("Sploitus response status for %s: %s", cve_id, response.status_code)

        if response.status_code != 200:
            logger.warning("Sploitus search failed for %s with HTTP %s", cve_id, response.status_code)
            # 如果無法訪問，返回一個搜尋URL作為替代
            return [search_url]
        
        # 解析 HTML 尋找 POC 連結
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 尋找可能包含 POC 的連結
        poc_links = []
        
        # 先查找所有的外部連結
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href', '').strip()
            text = link.get_text().strip().lower()
            
            # 跳過無關連結
            if not href or any(skip in href.lower() for skip in [
                'javascript:', 'mailto:', '#', 'sploitus.com/search', 'sploitus.com/?',
                'twitter.com', 'facebook.com', 'linkedin.com'
            ]):
                continue
            
            # 檢查是否為 POC 相關連結
            is_poc_link = False
            
            # 檢查 URL 是否包含 POC 相關關鍵字
            if any(keyword in href.lower() for keyword in [
                'github.com', 'gitlab.com', 'exploit-db.com', 'exploit',
                'packetstormsecurity.com', 'metasploit', 'nuclei-templates',
                'poc', 'cve', 'vulnerability'
            ]):
                is_poc_link = True
            
            # 檢查連結文字是否包含 POC 相關關鍵字
            if any(keyword in text for keyword in [
                'exploit', 'poc', 'github', 'gitlab', 'metasploit', 'nuclei'
            ]):
                is_poc_link = True
            
            if is_poc_link:
                # 處理相對連結
                if href.startswith('//'):
                    href = 'https:' + href
                elif href.startswith('/'):
                    href = f"https://sploitus.com{href}"
                
                # 檢查連結是否有效
                if href.startswith('http') and len(href) > 10:
                    poc_links.append(href)
        
        # 去重並限制數量
        unique_links = list(dict.fromkeys(poc_links))[:max_links]
        
        logger.info("Found %s POC links for %s", len(unique_links), cve_id)
        for i, link in enumerate(unique_links, 1):
            logger.debug("POC %s for %s: %s", i, cve_id, link)

        # 如果沒有找到任何連結，返回搜尋結果頁面
        if not unique_links:
            logger.info("No direct POC links for %s; returning search URL", cve_id)
            return [search_url]

        return unique_links
        
    except requests.RequestException as e:
        logger.warning("Network error searching POC for %s: %s", cve_id, e)
        # 網路錯誤時也返回搜尋URL
        return [f"https://sploitus.com/?query={cve_id.upper()}"]
    except Exception as e:
        logger.exception("Unhandled error searching POC for %s: %s", cve_id, e)
        return []


def batch_search_pocs(cve_list, delay=2):
    """
    批次搜尋多個 CVE 的 POC
    
    Args:
        cve_list: CVE 清單
        delay: 每次請求間的延遲秒數
        
    Returns:
        dict: {cve_id: [poc_links]}
    """
    results = {}
    
    for cve_id in cve_list:
        logger.info("Batch search for %s", cve_id)
        poc_links = search_sploitus_poc(cve_id)
        results[cve_id] = poc_links
        
        if poc_links:
            logger.debug("Found %s POC link(s) for %s", len(poc_links), cve_id)
        else:
            logger.debug("No POC links identified for %s", cve_id)
        
        # 延遲以避免被封
        if delay > 0:
            time.sleep(delay)
    
    return results

class SploitusClient:
    """Sploitus POC 查詢客戶端"""
    
    def __init__(self, rate_limit_delay=2):
        self.rate_limit_delay = rate_limit_delay
    
    def search_poc(self, cve_id, max_links=3):
        """
        搜尋單個 CVE 的 POC
        
        Args:
            cve_id: CVE 編號
            max_links: 最多返回的連結數量
            
        Returns:
            list: POC 連結清單
        """
        return search_sploitus_poc(cve_id, max_links)
    
    def batch_search(self, cve_list):
        """
        批次搜尋多個 CVE 的 POC
        
        Args:
            cve_list: CVE 清單
            
        Returns:
            dict: {cve_id: [poc_links]}
        """
        return batch_search_pocs(cve_list, self.rate_limit_delay)
