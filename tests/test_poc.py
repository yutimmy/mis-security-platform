#!/usr/bin/env python3
"""
測試 POC 查詢功能
"""

import sys
import os

# 確保能夠匯入專案模組並使用正確的路徑
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.chdir(project_root)

from crawlers.sploitus import SploitusClient

def test_poc_search():
    """測試 POC 搜尋功能"""
    print("測試 POC 搜尋功能...")
    
    # 創建客戶端
    client = SploitusClient(rate_limit_delay=1)
    
    # 測試一些常見的 CVE
    test_cves = [
        "CVE-2024-21762",  # Fortinet
        "CVE-2023-46747",  # 
        "CVE-2023-22515"   # Atlassian
    ]
    
    for cve_id in test_cves:
        print(f"\n搜尋 {cve_id}...")
        try:
            poc_links = client.search_poc(cve_id, max_links=2)
            if poc_links:
                print(f"  找到 {len(poc_links)} 個 POC 連結：")
                for i, link in enumerate(poc_links, 1):
                    print(f"    {i}. {link}")
            else:
                print(f"  未找到 POC")
        except Exception as e:
            print(f"  錯誤：{e}")

if __name__ == "__main__":
    test_poc_search()
