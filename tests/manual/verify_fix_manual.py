#!/usr/bin/env python3
# 快速驗證修復 - 檢查程式碼變更是否正確
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
    print("=== RSS 400 錯誤修復驗證 ===\n")
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    checks = [
        (
            os.path.join(base_path, "app/__init__.py"),
            "csrf.exempt(api_bp)",
            "API 藍圖已豁免 CSRF 保護"
        ),
        (
            os.path.join(base_path, "app/blueprints/api/views.py"),
            "request.get_json(silent=True)",
            "使用 silent=True 避免解析錯誤"
        ),
        (
            os.path.join(base_path, "app/blueprints/api/views.py"),
            "logger.exception",
            "使用 logger.exception 記錄完整錯誤"
        ),
        (
            os.path.join(base_path, "config.py"),
            "WTF_CSRF_ENABLED",
            "CSRF 配置已啟用"
        ),
    ]
    
    results = []
    for filepath, search_string, description in checks:
        result = check_file_contains(filepath, search_string, description)
        results.append(result)
    
    print("\n" + "="*50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ 所有檢查通過 ({passed}/{total})")
        print("\n下一步：")
        print("1. 啟動 Flask 應用程式：source .venv/bin/activate && python app.py")
        print("2. 執行測試：python tests/test_rss_api.py")
        return 0
    else:
        print(f"✗ 部分檢查失敗 ({passed}/{total})")
        print("\n請檢查上述失敗的項目")
        return 1


if __name__ == "__main__":
    sys.exit(main())
