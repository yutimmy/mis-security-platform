#!/usr/bin/env python3
"""
運行前檢查腳本
檢查環境設置、數據庫路徑、配置等是否正確
"""

import os
import subprocess
import sys


def check_environment():
    """檢查環境設置"""
    print("=== 環境檢查 ===")

    env_file = ".env"
    if os.path.exists(env_file):
        print("[OK] .env 檔案存在")
        with open(env_file, "r", encoding="utf-8") as fp:
            env_content = fp.read()

        required_vars = [
            "DEFAULT_ADMIN_USERNAME",
            "DEFAULT_ADMIN_PASSWORD",
            "SQLITE_PATH",
        ]
        missing_vars = [var for var in required_vars if var not in env_content]
        if missing_vars:
            print(f"[Fail] 缺少環境變數: {', '.join(missing_vars)}")
            return False
        print("[OK] 所有必要環境變數已設置")
    else:
        print("[Fail] .env 檔案不存在")
        return False

    return True


def check_database_path():
    """檢查數據庫路徑"""
    print("\n=== 數據庫路徑檢查 ===")

    try:
        sys.path.insert(0, os.getcwd())
        from config import Config

        db_path = Config.SQLITE_PATH
        print(f"數據庫路徑: {db_path}")
        print(f"路徑是絕對路徑: {os.path.isabs(db_path)}")

        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            print(f"創建數據庫目錄: {db_dir}")
            os.makedirs(db_dir, exist_ok=True)

        print(f"數據庫目錄存在: {os.path.exists(db_dir)}")
        print(f"數據庫檔案存在: {os.path.exists(db_path)}")
        return True

    except Exception as exc:  # pragma: no cover - manual utility
        print(f"[Fail] 數據庫路徑檢查失敗: {exc}")
        return False


def check_admin_config():
    """檢查管理員配置"""
    print("\n=== 管理員配置檢查 ===")

    try:
        from config import Config

        if not Config.DEFAULT_ADMIN_PASSWORD:
            print("[Fail] 管理員密碼未設置")
            return False

        print(f"[OK] 管理員用戶名: {Config.DEFAULT_ADMIN_USERNAME}")
        print(f"[OK] 管理員郵箱: {Config.DEFAULT_ADMIN_EMAIL}")
        print("[OK] 管理員密碼已設置")
        return True

    except Exception as exc:  # pragma: no cover - manual utility
        print(f"[Fail] 管理員配置檢查失敗: {exc}")
        return False


def test_imports():
    """測試關鍵模組導入"""
    print("\n=== 模組導入測試 ===")

    modules = [
        "config",
        "app",
        "app.models.db",
        "app.models.schema",
        "crawlers.extractors",
        "crawlers.cleaners",
        "utils.path_utils",
    ]

    failed = []
    for module in modules:
        try:
            __import__(module)
            print(f"[OK] {module}")
        except ImportError as exc:
            print(f"[Fail] {module}: {exc}")
            failed.append(module)

    return not failed


def run_unit_tests():
    """運行單元測試"""
    print("\n=== 單元測試 ===")

    script = """
import os
import sys

sys.path.insert(0, os.getcwd())

from tests.unit.test_crawler_utils import test_extract_cves_and_emails_are_sorted_and_unique


def main():
    test_extract_cves_and_emails_are_sorted_and_unique()


if __name__ == '__main__':
    main()
"""

    try:
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )

        if result.returncode == 0:
            print("[OK] 擷取器測試通過")
            if result.stdout:
                print(result.stdout)
        else:
            print("[Fail] 擷取器測試失敗")
            if result.stderr:
                print(result.stderr)
            return False

    except Exception as exc:  # pragma: no cover - manual utility
        print(f"[Fail] 測試運行失敗: {exc}")
        return False

    return True


def main():
    """主函數"""
    print("資安情訊平台 - 環境檢查")
    print("=" * 50)

    checks = [
        check_environment,
        check_database_path,
        check_admin_config,
        test_imports,
        run_unit_tests,
    ]

    all_passed = True
    for check in checks:
        if not check():
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("[OK] 所有檢查通過！系統已準備就緒。")
        print("\n可以執行以下命令初始化數據庫：")
        print("python init_db.py")
    else:
        print("[Fail] 部分檢查未通過，請修正後重新運行。")

    return all_passed


if __name__ == "__main__":  # pragma: no cover - manual utility
    sys.exit(0 if main() else 1)
