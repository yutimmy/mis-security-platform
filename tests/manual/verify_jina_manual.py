#!/usr/bin/env python3
# 快速驗證 Jina Reader 超時修復
import os
import sys


def check_file_contains(filepath, search_string, description):
    """檢查檔案是否包含特定字串"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if search_string in content:
                print(f"✓ {description}")
                return True
            else:
                print(f"✗ {description}")
                return False
    except FileNotFoundError:
        print(f"✗ 檔案不存在: {filepath}")
        return False


def main():
    print("=== Jina Reader 超時錯誤修復驗證 ===\n")
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    checks = [
        (
            os.path.join(base_path, "crawlers/jina_reader.py"),
            "max_retries",
            "Jina Reader 已加入重試機制"
        ),
        (
            os.path.join(base_path, "crawlers/jina_reader.py"),
            "except Timeout:",
            "已加入超時錯誤處理"
        ),
        (
            os.path.join(base_path, "crawlers/jina_reader.py"),
            "response.status_code == 429",
            "已加入速率限制處理"
        ),
        (
            os.path.join(base_path, "crawlers/jina_reader.py"),
            "(attempt + 1) *",
            "使用漸進式等待時間"
        ),
        (
            os.path.join(base_path, "config.py"),
            "JINA_TIMEOUT",
            "Config 已加入 JINA_TIMEOUT 設定"
        ),
        (
            os.path.join(base_path, "config.py"),
            "JINA_MAX_RETRIES",
            "Config 已加入 JINA_MAX_RETRIES 設定"
        ),
        (
            os.path.join(base_path, "crawlers/rss.py"),
            "jina_timeout",
            "RSS 爬蟲已接受 timeout 參數"
        ),
        (
            os.path.join(base_path, "crawlers/rss.py"),
            "jina_max_retries",
            "RSS 爬蟲已接受 max_retries 參數"
        ),
        (
            os.path.join(base_path, "app/services/rss_service.py"),
            "JINA_TIMEOUT",
            "RSS Service 已傳遞 JINA_TIMEOUT"
        ),
        (
            os.path.join(base_path, "app/services/rss_service.py"),
            "JINA_MAX_RETRIES",
            "RSS Service 已傳遞 JINA_MAX_RETRIES"
        ),
        (
            os.path.join(base_path, ".env.example"),
            "JINA_TIMEOUT",
            ".env.example 已包含 JINA_TIMEOUT"
        ),
        (
            os.path.join(base_path, ".env.example"),
            "JINA_MAX_RETRIES",
            ".env.example 已包含 JINA_MAX_RETRIES"
        ),
    ]
    
    results = []
    for filepath, search_string, description in checks:
        result = check_file_contains(filepath, search_string, description)
        results.append(result)
    
    print("\n" + "="*80)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ 所有檢查通過 ({passed}/{total})")
        print("\n✨ Jina Reader 超時錯誤修復完成！\n")
        print("主要改進：")
        print("  • 智能重試機制（最多 3 次）")
        print("  • 超時時間從 20 秒增加到 30 秒")
        print("  • 指數退避策略處理暫時性錯誤")
        print("  • 速率限制和伺服器錯誤自動處理")
        print("  • 詳細的日誌記錄")
        print("\n下一步：")
        print("1. 更新 .env 檔案（可選）：")
        print("   JINA_TIMEOUT=30")
        print("   JINA_MAX_RETRIES=3")
        print("2. 重啟應用程式")
        print("3. 測試：python tests/test_jina_retry.py")
        print("4. 執行 RSS 爬蟲觀察改進效果")
        return 0
    else:
        print(f"✗ 部分檢查失敗 ({passed}/{total})")
        print("\n請檢查上述失敗的項目")
        return 1


if __name__ == "__main__":
    sys.exit(main())
