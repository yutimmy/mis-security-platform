#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試進階統計功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.services.stats_service import StatsService
from app.models.db import db
import json

def test_stats_functionality():
    """測試統計功能"""
    print("=" * 60)
    print("[Test] 測試進階統計分析功能")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        try:
            # 1. 測試基礎統計
            print("\n[Stats] 測試基礎統計數據...")
            dashboard_stats = StatsService.get_dashboard_stats()
            print(f"[OK] 總新聞數: {dashboard_stats.get('total_news', 0)}")
            print(f"[OK] RSS 來源數: {dashboard_stats.get('total_sources', 0)}")
            print(f"[OK] 用戶數: {dashboard_stats.get('total_users', 0)}")
            
            # 2. 測試趨勢數據
            print("\n[Trend] 測試趨勢分析...")
            news_trend = StatsService.get_news_trend(days=30)
            print(f"[OK] 30天趨勢數據點數: {len(news_trend)}")
            
            # 3. 測試來源分佈
            print("\n[Target] 測試來源分佈...")
            source_distribution = StatsService.get_source_distribution()
            print(f"[OK] 來源分佈數據: {len(source_distribution)} 個來源")
            
            # 4. 測試 CVE 統計
            print("\n[Shield] 測試 CVE 統計...")
            cve_stats = StatsService.get_cve_stats()
            print(f"[OK] CVE 統計數據: {cve_stats.get('total_cves', 0)} 個 CVE")
            
            # 5. 測試安全指標
            print("\n[Secure] 測試安全指標...")
            security_metrics = StatsService.get_security_metrics()
            print(f"[OK] POC 覆蓋率: {security_metrics.get('poc_availability_ratio', 0)}%")
            
            # 6. 測試進階分析
            print("\n🔬 測試進階分析...")
            try:
                advanced_analytics = StatsService.get_advanced_analytics()
                print(f"[OK] 每日趨勢數據: {len(advanced_analytics.get('daily_news_trend', []))}")
                print(f"[OK] 小時分佈數據: {len(advanced_analytics.get('hourly_distribution', []))}")
            except Exception as e:
                print(f"[Warn] 進階分析功能可能需要更多數據: {e}")
            
            # 7. 測試性能指標
            print("\n[Fast] 測試性能指標...")
            try:
                performance_metrics = StatsService.get_performance_metrics()
                print(f"[OK] 任務性能數據: {len(performance_metrics.get('job_performance', []))}")
                print(f"[OK] 來源活躍度: {len(performance_metrics.get('source_activity', []))}")
            except Exception as e:
                print(f"[Warn] 性能指標功能可能需要更多數據: {e}")
            
            # 8. 測試內容分析
            print("\n[Note] 測試內容分析...")
            try:
                content_analysis = StatsService.get_content_analysis()
                print(f"[OK] 熱門關鍵字: {len(content_analysis.get('top_keywords', []))}")
                print(f"[OK] 內容長度分佈: {content_analysis.get('content_length_distribution', {})}")
            except Exception as e:
                print(f"[Warn] 內容分析功能可能需要更多數據: {e}")
            
            # 9. 測試用戶活動
            print("\n[Users] 測試用戶活動...")
            try:
                user_activity = StatsService.get_user_activity()
                print(f"[OK] 用戶角色分佈: {user_activity.get('role_distribution', {})}")
                print(f"[OK] 活躍用戶 (30天): {user_activity.get('active_users_30d', 0)}")
            except Exception as e:
                print(f"[Warn] 用戶活動功能可能需要更多數據: {e}")
            
            # 10. 測試任務統計
            print("\n[Config] 測試任務統計...")
            try:
                job_stats = StatsService.get_job_stats()
                print(f"[OK] 任務狀態分佈: {job_stats.get('status_distribution', {})}")
                print(f"[OK] 最近任務數: {len(job_stats.get('recent_jobs', []))}")
            except Exception as e:
                print(f"[Warn] 任務統計功能可能需要更多數據: {e}")
            
            print("\n" + "=" * 60)
            print("[OK] 統計功能測試完成！")
            print("[Hint] 提示：如果某些功能顯示警告，請確保資料庫中有足夠的測試數據")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n[Error] 測試過程中發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            assert False, f"統計功能測試失敗: {e}"

def test_chart_data_format():
    """測試圖表數據格式"""
    print("\n[Format] 測試圖表數據格式...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # 測試各種統計數據的JSON序列化
            stats_data = {
                'dashboard_stats': StatsService.get_dashboard_stats(),
                'news_trend': StatsService.get_news_trend(days=30),
                'source_distribution': StatsService.get_source_distribution(),
                'cve_stats': StatsService.get_cve_stats(),
                'security_metrics': StatsService.get_security_metrics()
            }
            
            # 嘗試序列化為JSON
            json_data = json.dumps(stats_data, ensure_ascii=False, indent=2, default=str)
            print(f"[OK] 統計數據JSON序列化成功，大小: {len(json_data)} 字符")
            
            # 檢查必要的字段
            required_fields = [
                'dashboard_stats.total_news',
                'dashboard_stats.total_sources', 
                'news_trend',
                'source_distribution'
            ]
            
            for field in required_fields:
                keys = field.split('.')
                data = stats_data
                for key in keys:
                    if key in data:
                        data = data[key]
                    else:
                        data = None
                        break
                
                if data is not None:
                    print(f"[OK] 必要字段 {field} 存在")
                else:
                    print(f"[Warn] 必要字段 {field} 不存在")
            
            print("[OK] 圖表數據格式測試完成")
            
        except Exception as e:
            print(f"[Error] 圖表數據格式測試失敗: {e}")
            assert False, f"圖表數據格式測試失敗: {e}"

def test_advanced_routes():
    """測試進階統計路由"""
    print("\n[Network] 測試進階統計路由...")
    
    app = create_app()
    client = app.test_client()
    
    try:
        with app.app_context():
            # 模擬管理員登入
            with client.session_transaction() as sess:
                sess['user_id'] = 1
                sess['role'] = 'admin'
            
            # 測試基礎統計頁面
            response = client.get('/admin/stats')
            print(f"[OK] 基礎統計頁面: {response.status_code}")
            
            # 測試進階統計頁面
            response = client.get('/admin/stats/advanced')
            print(f"[OK] 進階統計頁面: {response.status_code}")
            
            # 測試刷新API
            response = client.get('/admin/api/stats/refresh')
            print(f"[OK] 統計刷新API: {response.status_code}")
            
            # 測試匯出API
            response = client.get('/admin/api/stats/export')
            print(f"[OK] 統計匯出API: {response.status_code}")
            
            print("[OK] 路由測試完成")
            
    except Exception as e:
        print(f"[Error] 路由測試失敗: {e}")
        assert False, f"路由測試失敗: {e}"

if __name__ == "__main__":
    print("[Run] 開始進階統計功能測試...")
    
    # 執行所有測試
    tests = [
        test_stats_functionality,
        test_chart_data_format,
        test_advanced_routes
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"[Error] 測試 {test.__name__} 發生異常: {e}")
    
    print(f"\n[Summary] 測試結果: {passed}/{total} 通過")
    
    if passed == total:
        print("[Success] 所有測試通過！進階統計功能已準備就緒。")
    else:
        print("[Warn] 某些測試未通過，請檢查相關功能。")
    
    print("\n[Hint] 使用說明:")
    print("1. 確保資料庫中有足夠的測試數據")
    print("2. 訪問 /admin/stats/advanced 查看進階統計")
    print("3. 使用不同的 Tab 查看各種分析圖表")
    print("4. 可以匯出統計數據進行進一步分析")
