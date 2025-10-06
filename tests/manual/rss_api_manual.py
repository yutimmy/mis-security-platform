# 測試 RSS API 端點
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests


def test_rss_api():
    """測試 RSS 爬蟲 API 端點"""
    base_url = "http://127.0.0.1:5000"
    
    # 建立測試 session
    session = requests.Session()
    
    # 1. 先登入（假設有測試帳號）
    print("1. 測試登入...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    login_response = session.post(f"{base_url}/auth/login", data=login_data)
    print(f"   登入狀態碼: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print("   登入失敗，無法繼續測試")
        return
    
    # 2. 測試觸發 RSS 爬蟲（不帶參數）
    print("\n2. 測試觸發 RSS 爬蟲（全部來源）...")
    rss_response = session.post(f"{base_url}/api/jobs/rss")
    print(f"   狀態碼: {rss_response.status_code}")
    print(f"   回應: {rss_response.text[:500]}")
    
    if rss_response.status_code == 200:
        data = rss_response.json()
        print(f"   成功: {data.get('message', 'N/A')}")
        print(f"   Job ID: {data.get('data', {}).get('job_run_id', 'N/A')}")
    else:
        print(f"   失敗: {rss_response.text}")
    
    # 3. 測試觸發 RSS 爬蟲（指定來源）
    print("\n3. 測試觸發 RSS 爬蟲（指定來源 ID=1）...")
    rss_response_single = session.post(
        f"{base_url}/api/jobs/rss",
        json={"rss_id": 1}
    )
    print(f"   狀態碼: {rss_response_single.status_code}")
    print(f"   回應: {rss_response_single.text[:500]}")
    
    # 4. 測試健康檢查
    print("\n4. 測試健康檢查...")
    health_response = session.get(f"{base_url}/api/healthz")
    print(f"   狀態碼: {health_response.status_code}")
    print(f"   回應: {health_response.json()}")


if __name__ == "__main__":
    print("=== RSS API 測試 ===\n")
    print("請確保 Flask 應用程式正在運行於 http://127.0.0.1:5000")
    print("且資料庫中有 admin/admin123 測試帳號\n")
    
    try:
        test_rss_api()
    except requests.exceptions.ConnectionError:
        print("\n錯誤：無法連接到 Flask 應用程式")
        print("請先執行：source .venv/bin/activate && python app.py")
    except Exception as e:
        print(f"\n測試過程中發生錯誤：{e}")
        import traceback
        traceback.print_exc()
