# 統計分析服務
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

from sqlalchemy import func

from config import Config
from ..models.db import db
from ..models.schema import News, RssSource, JobRun, User, CvePoc


UTC = ZoneInfo("UTC")
try:
    APP_TZ = ZoneInfo(getattr(Config, "TIMEZONE", "UTC"))
except Exception:
    APP_TZ = UTC


def _to_utc_naive(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(UTC).replace(tzinfo=None)


def _to_local(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(APP_TZ)


class StatsService:
    """提供各種統計分析功能"""

    @staticmethod
    def get_dashboard_stats():
        """取得儀表板統計數據"""
        now_local = datetime.now(APP_TZ)
        week_ago = _to_utc_naive(now_local - timedelta(days=7))
        month_ago = _to_utc_naive(now_local - timedelta(days=30))

        # 基本統計
        total_news = db.session.query(func.count(News.id)).scalar() or 0
        total_sources = db.session.query(func.count(RssSource.id)).scalar() or 0
        total_users = db.session.query(func.count(User.id)).scalar() or 0
        total_cves = db.session.query(func.count(CvePoc.id)).scalar() or 0

        # 本週統計
        week_news = db.session.query(func.count(News.id)).filter(
            News.created_at >= week_ago
        ).scalar() or 0

        # 本月統計
        month_news = db.session.query(func.count(News.id)).filter(
            News.created_at >= month_ago
        ).scalar() or 0

        # 任務統計
        total_jobs = db.session.query(func.count(JobRun.id)).scalar() or 0
        success_jobs = db.session.query(func.count(JobRun.id)).filter(
            JobRun.status == 'success'
        ).scalar() or 0
        failed_jobs = db.session.query(func.count(JobRun.id)).filter(
            JobRun.status == 'failed'
        ).scalar() or 0
        running_jobs = db.session.query(func.count(JobRun.id)).filter(
            JobRun.status == 'running'
        ).scalar() or 0
        
        # 待審核用戶數
        pending_users = db.session.query(func.count(User.id)).filter(
            User.is_active == False
        ).scalar() or 0

        return {
            'total_news': total_news,
            'total_sources': total_sources,
            'total_users': total_users,
            'total_cves': total_cves,
            'week_news': week_news,
            'month_news': month_news,
            'total_jobs': total_jobs,
            'success_jobs': success_jobs,
            'failed_jobs': failed_jobs,
            'running_jobs': running_jobs,
            'pending_users': pending_users
        }

    @staticmethod
    def get_news_trend(days=30):
        """取得新聞數量趨勢（按日）"""
        end_local = datetime.now(APP_TZ)
        start_local_date = end_local.date() - timedelta(days=days)
        start_local = datetime.combine(start_local_date, time.min, tzinfo=APP_TZ)
        start_utc = _to_utc_naive(start_local)

        news_rows = db.session.query(News.created_at).filter(
            News.created_at >= start_utc
        ).all()

        counts = {}
        for (created_at,) in news_rows:
            local_date = _to_local(created_at)
            if local_date is None:
                continue
            date_key = local_date.date()
            counts[date_key] = counts.get(date_key, 0) + 1

        trend_data = []
        current_date = start_local_date
        end_date = end_local.date()
        while current_date <= end_date:
            trend_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'count': counts.get(current_date, 0)
            })
            current_date += timedelta(days=1)

        return trend_data

    @staticmethod
    def get_source_distribution():
        """取得來源分佈統計"""
        # 直接從 News 表統計 source 欄位
        results = db.session.query(
            News.source,
            func.count(News.id).label('count')
        ).group_by(News.source
        ).order_by(func.count(News.id).desc()).all()

        return [
            {
                'name': r.source,
                'count': r.count
            }
            for r in results
        ]

    @staticmethod
    def get_cve_stats():
        """取得 CVE 相關統計"""
        # CVE 狀態分佈（從有 POC 連結判斷）
        total_cves = db.session.query(func.count(News.id)).filter(
            News.cve_id.isnot(None),
            News.cve_id != ''
        ).scalar() or 0
        
        cves_with_poc = db.session.query(func.count(News.id)).filter(
            News.cve_id.isnot(None),
            News.cve_id != '',
            News.poc_link.isnot(None),
            News.poc_link != ''
        ).scalar() or 0
        
        cves_without_poc = total_cves - cves_with_poc

        status_dist = {
            'with_poc': cves_with_poc,
            'without_poc': cves_without_poc
        }

        # 最近發現的 CVE（從 News 表抓取）
        recent_news_with_cve = db.session.query(News).filter(
            News.cve_id.isnot(None),
            News.cve_id != ''
        ).order_by(News.created_at.desc()).limit(10).all()

        recent_cves = []
        for news in recent_news_with_cve:
            if news.cve_id:
                # 處理可能有多個 CVE 的情況
                cve_list = news.cve_id.split(',') if ',' in news.cve_id else [news.cve_id]
                for cve in cve_list:
                    cve = cve.strip()
                    if cve and len(recent_cves) < 10:
                        created_local = _to_local(news.created_at)
                        recent_cves.append({
                            'cve_id': cve,
                            'news_title': news.title,
                            'has_poc': bool(news.poc_link),
                            'created_at': created_local.strftime('%Y-%m-%d') if created_local else None
                        })

        return {
            'status_distribution': status_dist,
            'recent_cves': recent_cves[:10],
            'total_cves': total_cves
        }

    @staticmethod
    def get_user_activity():
        """取得用戶活動統計"""
        # 用戶角色分佈
        role_distribution = {}
        users = db.session.query(User.role, func.count(User.id)).group_by(User.role).all()
        for role, count in users:
            role_distribution[role or 'unknown'] = count
        
        # 用戶活躍度（最近30天登入）
        thirty_days_ago = _to_utc_naive(datetime.now(APP_TZ) - timedelta(days=30))
        active_users = db.session.query(func.count(User.id)).filter(
            User.updated_at >= thirty_days_ago
        ).scalar() or 0
        
        # 新註冊用戶（最近7天）
        week_ago = _to_utc_naive(datetime.now(APP_TZ) - timedelta(days=7))
        new_users = db.session.query(func.count(User.id)).filter(
            User.created_at >= week_ago
        ).scalar() or 0
        
        return {
            'role_distribution': role_distribution,
            'active_users_30d': active_users,
            'new_users_7d': new_users,
            'total_users': db.session.query(func.count(User.id)).scalar() or 0
        }

    @staticmethod
    def get_job_statistics():
        """取得任務執行統計"""
        # 任務成功率
        total_jobs = db.session.query(func.count(JobRun.id)).scalar() or 0
        success_jobs = db.session.query(func.count(JobRun.id)).filter(
            JobRun.status == 'success'
        ).scalar() or 0
        failed_jobs = db.session.query(func.count(JobRun.id)).filter(
            JobRun.status == 'failed'
        ).scalar() or 0
        running_jobs = db.session.query(func.count(JobRun.id)).filter(
            JobRun.status == 'running'
        ).scalar() or 0
        partial_jobs = db.session.query(func.count(JobRun.id)).filter(
            JobRun.status == 'partial'
        ).scalar() or 0
        
        success_rate = (success_jobs / total_jobs * 100) if total_jobs > 0 else 0
        
        # 任務類型分佈
        job_type_dist = db.session.query(
            JobRun.job_type,
            func.count(JobRun.id).label('count')
        ).group_by(JobRun.job_type).all()
        
        # 最近任務執行記錄
        recent_jobs = db.session.query(JobRun).order_by(
            JobRun.started_at.desc()
        ).limit(5).all()

        # 每日任務執行趨勢（依據設定時區）
        week_ago_local = datetime.now(APP_TZ) - timedelta(days=7)
        week_ago_utc = _to_utc_naive(week_ago_local)

        job_rows = db.session.query(JobRun.started_at).filter(
            JobRun.started_at >= week_ago_utc
        ).all()

        job_counts = {}
        for (started_at,) in job_rows:
            local_date = _to_local(started_at)
            if local_date is None:
                continue
            key = local_date.date()
            job_counts[key] = job_counts.get(key, 0) + 1

        job_trend = []
        current_date = week_ago_local.date()
        end_date = datetime.now(APP_TZ).date()
        while current_date <= end_date:
            job_trend.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'count': job_counts.get(current_date, 0)
            })
            current_date += timedelta(days=1)

        return {
            'total_jobs': total_jobs,
            'success_jobs': success_jobs,
            'failed_jobs': failed_jobs,
            'running_jobs': running_jobs,
            'partial_jobs': partial_jobs,
            'success_rate': round(success_rate, 1),
            'job_type_distribution': {r.job_type: r.count for r in job_type_dist},
            'daily_trend': job_trend,
            'recent_jobs': [
                {
                    'id': job.id,
                    'job_type': job.job_type,
                    'status': job.status,
                    'started_at': (_to_local(job.started_at).strftime('%Y-%m-%d %H:%M')
                                   if job.started_at else None),
                    'inserted_count': job.inserted_count,
                    'error_count': job.error_count
                }
                for job in recent_jobs
            ]
        }

    @staticmethod
    def get_job_stats():
        """取得任務統計 (別名)"""
        return StatsService.get_job_statistics()

    @staticmethod
    def get_category_stats():
        """取得分類統計 (別名)"""
        return StatsService.get_category_statistics()

    @staticmethod
    def get_category_statistics():
        """取得類別統計（樹狀結構數據）"""
        # RSS 來源分類統計
        category_stats = db.session.query(
            RssSource.category,
            func.count(RssSource.id).label('source_count')
        ).filter(
            RssSource.enabled == True
        ).group_by(RssSource.category).all()
        
        # 為每個分類獲取新聞數量
        category_data = []
        for cat_stat in category_stats:
            category = cat_stat.category or 'other'
            source_count = cat_stat.source_count
            
            # 獲取該分類下的新聞數量
            news_count = db.session.query(func.count(News.id)).join(
                RssSource, News.source == RssSource.source
            ).filter(
                RssSource.category == category,
                RssSource.enabled == True
            ).scalar() or 0
            
            category_data.append({
                'name': category,
                'source_count': source_count,
                'news_count': news_count,
                'children': []
            })
        
        return category_data

    @staticmethod
    def get_security_metrics():
        """取得安全指標統計"""
        # CVE 嚴重性分佈（假設從 CVE ID 可以推斷年份）
        cve_years = {}
        news_with_cve = db.session.query(News).filter(
            News.cve_id.isnot(None),
            News.cve_id != ''
        ).all()
        
        for news in news_with_cve:
            if news.cve_id:
                cve_list = news.cve_id.split(',') if ',' in news.cve_id else [news.cve_id]
                for cve in cve_list:
                    cve = cve.strip()
                    if cve.startswith('CVE-'):
                        try:
                            year = cve.split('-')[1]
                            if year.isdigit():
                                cve_years[year] = cve_years.get(year, 0) + 1
                        except IndexError:
                            continue
        
        # Email 洩露統計
        email_count = db.session.query(func.count(News.id)).filter(
            News.email.isnot(None),
            News.email != ''
        ).scalar() or 0
        
        # POC 可用性比率
        total_cve_news = db.session.query(func.count(News.id)).filter(
            News.cve_id.isnot(None),
            News.cve_id != ''
        ).scalar() or 0
        
        poc_available = db.session.query(func.count(News.id)).filter(
            News.cve_id.isnot(None),
            News.cve_id != '',
            News.poc_link.isnot(None),
            News.poc_link != ''
        ).scalar() or 0
        
        poc_ratio = (poc_available / total_cve_news * 100) if total_cve_news > 0 else 0
        
        return {
            'cve_by_year': cve_years,
            'email_disclosures': email_count,
            'poc_availability_ratio': round(poc_ratio, 1),
            'total_cve_news': total_cve_news,
            'poc_available_count': poc_available
        }

    @staticmethod
    def get_advanced_analytics():
        """取得進階分析數據"""
        now_local = datetime.now(APP_TZ)
        thirty_days_ago_local = now_local - timedelta(days=30)
        start_local = datetime.combine(thirty_days_ago_local.date(), time.min, tzinfo=APP_TZ)
        start_utc = _to_utc_naive(start_local)

        news_rows = db.session.query(News.created_at, News.cve_id).filter(
            News.created_at >= start_utc
        ).all()

        daily_counts = {}
        hourly_counts = {hour: 0 for hour in range(24)}
        cve_trends = {}

        for created_at, cve_id in news_rows:
            local_dt = _to_local(created_at)
            if local_dt is None:
                continue

            date_key = local_dt.date()
            daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
            hourly_counts[local_dt.hour] += 1

            if cve_id:
                for raw_cve in cve_id.split(','):
                    cve = raw_cve.strip()
                    if not cve:
                        continue
                    date_str = local_dt.strftime('%Y-%m-%d')
                    cve_trends[date_str] = cve_trends.get(date_str, 0) + 1

        daily_news_trend = []
        current_date = thirty_days_ago_local.date()
        end_date = now_local.date()
        while current_date <= end_date:
            daily_news_trend.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'count': daily_counts.get(current_date, 0)
            })
            current_date += timedelta(days=1)

        return {
            'daily_news_trend': daily_news_trend,
            'hourly_distribution': [
                {'hour': hour, 'count': count}
                for hour, count in sorted(hourly_counts.items())
            ],
            'cve_daily_trend': [
                {'date': date, 'count': count}
                for date, count in sorted(cve_trends.items())
            ]
        }

    @staticmethod
    def get_performance_metrics():
        """取得系統性能指標"""
        now_local = datetime.now(APP_TZ)
        week_ago = _to_utc_naive(now_local - timedelta(days=7))
        
        # 任務執行性能
        job_performance = db.session.query(
            JobRun.job_type,
            func.avg(func.julianday(JobRun.ended_at) - func.julianday(JobRun.started_at)).label('avg_duration'),
            func.count(JobRun.id).label('total_runs'),
            func.sum(JobRun.inserted_count).label('total_insertions'),
            func.sum(JobRun.error_count).label('total_errors')
        ).filter(
            JobRun.started_at >= week_ago,
            JobRun.ended_at.isnot(None)
        ).group_by(JobRun.job_type).all()
        
        # RSS 來源活躍度
        source_activity = db.session.query(
            RssSource.name,
            RssSource.source,
            func.count(News.id).label('news_count'),
            func.max(News.created_at).label('last_update')
        ).outerjoin(
            News, News.source == RssSource.source
        ).filter(
            RssSource.enabled == True
        ).group_by(
            RssSource.id, RssSource.name, RssSource.source
        ).order_by(func.count(News.id).desc()).all()
        
        return {
            'job_performance': [
                {
                    'type': r.job_type,
                    'avg_duration_minutes': round((r.avg_duration or 0) * 24 * 60, 2),
                    'total_runs': r.total_runs,
                    'total_insertions': r.total_insertions or 0,
                    'total_errors': r.total_errors or 0,
                    'success_rate': round((r.total_runs - (r.total_errors or 0)) / r.total_runs * 100, 1) if r.total_runs > 0 else 0
                }
                for r in job_performance
            ],
            'source_activity': [
                {
                    'name': r.name,
                    'source': r.source,
                    'news_count': r.news_count,
                    'last_update': (_to_local(r.last_update).strftime('%Y-%m-%d %H:%M')
                                   if r.last_update else 'Never'),
                    'status': 'active' if r.news_count > 0 else 'inactive'
                }
                for r in source_activity
            ]
        }

    @staticmethod
    def get_content_analysis():
        """取得內容分析統計"""
        # 關鍵字頻率分析
        keyword_frequency = {}
        news_with_keywords = db.session.query(News).filter(
            News.keyword.isnot(None),
            News.keyword != ''
        ).limit(1000).all()  # 限制數量避免性能問題
        
        for news in news_with_keywords:
            if news.keyword:
                # 嘗試解析 JSON 格式的關鍵字
                try:
                    import json
                    keywords = json.loads(news.keyword)
                    if isinstance(keywords, list):
                        for keyword in keywords:
                            keyword = keyword.strip().lower()
                            keyword_frequency[keyword] = keyword_frequency.get(keyword, 0) + 1
                except:
                    # 如果不是 JSON，嘗試以逗號分隔
                    keywords = news.keyword.split(',')
                    for keyword in keywords:
                        keyword = keyword.strip().lower()
                        if keyword:
                            keyword_frequency[keyword] = keyword_frequency.get(keyword, 0) + 1
        
        # 內容長度分佈
        content_lengths = db.session.query(
            func.length(News.content).label('length')
        ).filter(
            News.content.isnot(None),
            News.content != ''
        ).all()
        
        # 分組統計內容長度
        length_distribution = {
            'short': 0,    # < 500 字
            'medium': 0,   # 500-2000 字
            'long': 0,     # 2000-5000 字
            'very_long': 0 # > 5000 字
        }
        
        for length_record in content_lengths:
            length = length_record.length or 0
            if length < 500:
                length_distribution['short'] += 1
            elif length < 2000:
                length_distribution['medium'] += 1
            elif length < 5000:
                length_distribution['long'] += 1
            else:
                length_distribution['very_long'] += 1
        
        return {
            'top_keywords': sorted(
                [{'keyword': k, 'count': v} for k, v in keyword_frequency.items()],
                key=lambda x: x['count'],
                reverse=True
            )[:20],
            'content_length_distribution': length_distribution
        }

    @staticmethod
    def get_current_timestamp():
        """取得當前時間戳"""
        return datetime.utcnow().strftime('%Y%m%d_%H%M%S')
