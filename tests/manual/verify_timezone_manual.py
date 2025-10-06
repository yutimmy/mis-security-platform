#!/usr/bin/env python3
# 快速驗證時區修復
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


def check_file_not_contains(filepath, search_string, description):
    """檢查檔案不應包含特定字串"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if search_string not in content:
                print(f"✓ {description}")
                return True
            else:
                print(f"✗ {description}")
                return False
    except FileNotFoundError:
        print(f"✗ 檔案不存在: {filepath}")
        return False


def main():
    print("=== 時區修復驗證 ===\n")
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    checks = [
        # 1. 檢查工具函數存在
        (
            True,
            os.path.join(base_path, "utils/timezone_utils.py"),
            "get_current_time",
            "時區工具已建立"
        ),
        (
            True,
            os.path.join(base_path, "utils/timezone_utils.py"),
            "def now_with_tz",
            "now_with_tz 函數已實作"
        ),
        
        # 2. 檢查 schema 使用新函數
        (
            True,
            os.path.join(base_path, "app/models/schema.py"),
            "_get_current_time",
            "Schema 使用本地時間函數"
        ),
        (
            False,
            os.path.join(base_path, "app/models/schema.py"),
            "datetime.utcnow",
            "Schema 已移除 datetime.utcnow"
        ),
        
        # 3. 檢查服務層
        (
            True,
            os.path.join(base_path, "app/services/rss_service.py"),
            "from utils.timezone_utils import get_current_time",
            "RSS Service 已匯入時區工具"
        ),
        (
            True,
            os.path.join(base_path, "app/services/rss_service.py"),
            "def _now():",
            "RSS Service 使用 _now() 函數"
        ),
        (
            True,
            os.path.join(base_path, "app/services/poc_service.py"),
            "from utils.timezone_utils import get_current_time",
            "POC Service 已匯入時區工具"
        ),
        
        # 4. 檢查 API views
        (
            True,
            os.path.join(base_path, "app/blueprints/api/views.py"),
            "from utils.timezone_utils import get_current_time",
            "API Views 已匯入時區工具"
        ),
        (
            True,
            os.path.join(base_path, "app/blueprints/api/views.py"),
            "def _now():",
            "API Views 使用 _now() 函數"
        ),
    ]
    
    results = []
    for should_contain, filepath, search_string, description in checks:
        if should_contain:
            result = check_file_contains(filepath, search_string, description)
        else:
            result = check_file_not_contains(filepath, search_string, description)
        results.append(result)
    
    print("\n" + "="*80)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ 所有檢查通過 ({passed}/{total})")
        print("\n✨ 時區修復完成！\n")
        print("主要改進：")
        print("  • 新增時區工具模組（utils/timezone_utils.py）")
        print("  • 資料庫記錄使用本地時間（UTC+8）而非 UTC")
        print("  • 所有服務層統一使用時區函數")
        print("  • 支援時區轉換和格式化")
        print("\n下一步：")
        print("1. 執行測試：python tests/test_timezone.py")
        print("2. 重啟應用程式")
        print("3. 執行 RSS 爬蟲並檢查時間記錄")
        print("4. 確認時間顯示為 UTC+8（台北時間）")
        return 0
    else:
        print(f"✗ 部分檢查失敗 ({passed}/{total})")
        print("\n請檢查上述失敗的項目")
        return 1


if __name__ == "__main__":
    sys.exit(main())
