# 測試改進後的 Jina Reader
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from crawlers.jina_reader import fetch_readable


def test_jina_reader():
    """測試 Jina Reader 的重試和錯誤處理"""
    
    print("=== Jina Reader 測試 ===\n")
    
    # 測試案例
    test_urls = [
        {
            "url": "https://www.bleepingcomputer.com/news/security/new-python-backdoor/",
            "description": "正常的 URL（較短）"
        },
        {
            "url": "https://www.bleepingcomputer.com/news/artificial-intelligence/openai-wants-chatgpt-to-be-your-emotional-support/",
            "description": "之前超時的 URL（較長）"
        },
        {
            "url": "https://invalid-domain-that-does-not-exist-12345.com/",
            "description": "無效的域名"
        }
    ]
    
    for i, test in enumerate(test_urls, 1):
        print(f"\n測試 {i}: {test['description']}")
        print(f"URL: {test['url'][:80]}...")
        print("-" * 80)
        
        try:
            # 使用較短的超時時間來加快測試
            content = fetch_readable(
                test['url'],
                rpm=60,  # 高 RPM 用於測試
                max_retries=2,  # 減少重試次數加快測試
                timeout=15  # 較短的超時時間
            )
            
            if content:
                print(f"✓ 成功獲取內容")
                print(f"  內容長度: {len(content)} 字元")
                print(f"  前 200 字元: {content[:200]}...")
            else:
                print(f"✗ 未能獲取內容（可能是網路問題或速率限制）")
                
        except Exception as e:
            print(f"✗ 發生錯誤: {e}")
    
    print("\n" + "=" * 80)
    print("測試完成！")
    print("\n說明：")
    print("- 正常情況下應該能夠獲取內容")
    print("- 超時或網路錯誤會自動重試")
    print("- 超過最大重試次數後會返回空字串")
    print("- 所有錯誤都會被適當記錄")


if __name__ == "__main__":
    test_jina_reader()
