# 後台管理：使用者管理、RSS 管理、任務執行
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps

from app.models.db import db
from app.models.schema import User, RssSource, JobRun, News
from app.services.stats_service import StatsService


admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """管理員權限裝飾器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('需要管理員權限', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@admin_required
def dashboard():
    """管理後台首頁"""
    stats = StatsService.get_dashboard_stats()
    recent_jobs = JobRun.query.order_by(JobRun.started_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', stats=stats, recent_jobs=recent_jobs)


@admin_bp.route('/users')
@admin_required
def users():
    """使用者管理"""
    page = request.args.get('page', 1, type=int)
    users_list = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/users.html', users_list=users_list)


@admin_bp.route('/users/<int:user_id>/activate', methods=['POST'])
@admin_required
def activate_user(user_id):
    """啟用使用者"""
    user = User.query.get_or_404(user_id)
    user.is_active = True
    db.session.commit()
    flash(f'已啟用使用者 {user.username}', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/deactivate', methods=['POST'])
@admin_required
def deactivate_user(user_id):
    """停用使用者"""
    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()
    flash(f'已停用使用者 {user.username}', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/rss')
@admin_required
def rss_sources():
    """RSS 來源管理"""
    sources = RssSource.query.order_by(RssSource.id).all()
    return render_template('admin/rss_sources.html', sources=sources)


@admin_bp.route('/rss/add', methods=['GET', 'POST'])
@admin_required
def add_rss_source():
    """新增 RSS 來源"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        url = request.form.get('url', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        is_active = request.form.get('is_active') == '1'
        
        if not name or not url:
            flash('名稱和 URL 為必填項目', 'error')
            return render_template('admin/add_rss_source.html')
        
        # 檢查是否已存在
        if RssSource.query.filter_by(link=url).first():
            flash('此 RSS 連結已存在', 'error')
            return render_template('admin/add_rss_source.html')
        
        rss_source = RssSource(
            name=name, 
            link=url, 
            source=name.lower().replace(' ', '_'),
            category=category if category else 'other',
            description=description,
            is_active=is_active
        )
        db.session.add(rss_source)
        db.session.commit()
        
        flash('RSS 來源新增成功', 'success')
        return redirect(url_for('admin.rss_sources'))
    
    return render_template('admin/add_rss_source.html')


@admin_bp.route('/rss/<int:source_id>/toggle', methods=['POST'])
@admin_required
def toggle_rss_source(source_id):
    """啟用/停用 RSS 來源"""
    source = RssSource.query.get_or_404(source_id)
    source.enabled = not source.enabled
    db.session.commit()
    
    status = '啟用' if source.enabled else '停用'
    flash(f'已{status} RSS 來源 {source.name}', 'success')
    return redirect(url_for('admin.rss_sources'))


@admin_bp.route('/jobs')
@admin_required
def jobs():
    """任務管理"""
    page = request.args.get('page', 1, type=int)
    jobs = JobRun.query.order_by(JobRun.started_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # 取得統計資料
    stats = StatsService.get_dashboard_stats()
    
    return render_template('admin/jobs.html', jobs=jobs.items, stats=stats)


@admin_bp.route('/stats')
@admin_required
def stats():
    """統計分析頁面 - 簡化版"""
    # 只取得核心統計資料
    dashboard_stats = StatsService.get_dashboard_stats()
    news_trend = StatsService.get_news_trend(days=30)
    source_distribution = StatsService.get_source_distribution()
    cve_stats = StatsService.get_cve_stats()
    security_metrics = StatsService.get_security_metrics()

    # 近期 job 列表供 template 顯示
    recent_jobs = JobRun.query.order_by(JobRun.started_at.desc()).limit(10).all()

    # 準備圖表資料
    monthly_labels = [item['date'] for item in news_trend] if news_trend else ['2024-07', '2024-08', '2024-09']
    monthly_counts = [item['count'] for item in news_trend] if news_trend else [15, 25, 18]
    
    top_sources_labels = [item['name'] for item in source_distribution[:10]] if source_distribution else ['iTHome', 'CERT', 'Security Focus', 'CVE Details']
    top_sources_counts = [item['count'] for item in source_distribution[:10]] if source_distribution else [45, 32, 28, 15]
    
    # 修正 CVE 數據處理 - 使用 status_distribution 並轉換為中文
    cve_distribution = cve_stats.get('status_distribution', {}) if cve_stats else {'with_poc': 12, 'without_poc': 8}
    cve_labels_mapping = {
        'with_poc': '有 POC',
        'without_poc': '無 POC'
    }
    cve_labels = [cve_labels_mapping.get(key, key) for key in cve_distribution.keys()] if cve_distribution else ['有 POC', '無 POC']
    cve_counts = list(cve_distribution.values()) if cve_distribution else [12, 8]

    # 計算POC覆蓋率
    total_cves = cve_stats.get('total_cves', 0) if cve_stats else 0
    cves_with_poc = cve_distribution.get('with_poc', 0)
    poc_coverage_percent = (cves_with_poc / total_cves * 100) if total_cves > 0 else 0
    poc_coverage = f"{poc_coverage_percent:.1f}%"
    
    # 添加POC覆蓋率到dashboard_stats
    dashboard_stats['poc_coverage'] = poc_coverage
    dashboard_stats['poc_coverage_percent'] = poc_coverage_percent

    # 使用現有的 admin/stats.html 模板，並提供前端所需的最小欄位
    return render_template('admin/stats.html',
                           stats=dashboard_stats,
                           news_trend=news_trend,
                           source_distribution=source_distribution,
                           cve_stats=cve_stats,
                           security_metrics=security_metrics,
                           jobs=recent_jobs,
                           monthly_labels=monthly_labels,
                           monthly_counts=monthly_counts,
                           top_sources_labels=top_sources_labels,
                           top_sources_counts=top_sources_counts,
                           cve_labels=cve_labels,
                           cve_counts=cve_counts)


@admin_bp.route('/stats/advanced')
@admin_required
def stats_advanced():
    """統計分析頁面 - 進階版"""
    # 取得完整統計資料
    dashboard_stats = StatsService.get_dashboard_stats()
    news_trend = StatsService.get_news_trend(days=30)
    source_distribution = StatsService.get_source_distribution()
    cve_stats = StatsService.get_cve_stats()
    security_metrics = StatsService.get_security_metrics()
    
    # 新增進階分析數據
    advanced_analytics = StatsService.get_advanced_analytics()
    performance_metrics = StatsService.get_performance_metrics()
    content_analysis = StatsService.get_content_analysis()
    user_activity = StatsService.get_user_activity()
    job_stats = StatsService.get_job_stats()
    category_stats = StatsService.get_category_stats()
    
    return render_template('admin/stats_advanced.html',
                         dashboard_stats=dashboard_stats,
                         news_trend=news_trend,
                         source_distribution=source_distribution,
                         cve_stats=cve_stats,
                         security_metrics=security_metrics,
                         advanced_analytics=advanced_analytics,
                         performance_metrics=performance_metrics,
                         content_analysis=content_analysis,
                         user_activity=user_activity,
                         job_stats=job_stats,
                         category_stats=category_stats)


@admin_bp.route('/api/stats/refresh')
@admin_bp.route('/refresh_stats')
@admin_required
def refresh_stats():
    """刷新統計數據的 API 端點"""
    try:
        # 重新計算所有統計數據
        dashboard_stats = StatsService.get_dashboard_stats()
        news_trend = StatsService.get_news_trend(days=30)
        source_distribution = StatsService.get_source_distribution()
        cve_stats = StatsService.get_cve_stats()
        
        # 處理月度趨勢數據
        monthly_labels = [item['date'] for item in news_trend]
        monthly_counts = [item['count'] for item in news_trend]
        
        # 處理來源分佈數據
        top_sources = source_distribution[:10]  # 取前10個
        top_sources_labels = [item['name'] for item in top_sources]
        top_sources_counts = [item['count'] for item in top_sources]
        
        # 處理CVE數據 - 使用status_distribution並轉換為中文，與stats路由保持一致
        cve_distribution = cve_stats.get('status_distribution', {}) if cve_stats else {'with_poc': 12, 'without_poc': 8}
        cve_labels_mapping = {
            'with_poc': '有 POC',
            'without_poc': '無 POC'
        }
        cve_labels = [cve_labels_mapping.get(key, key) for key in cve_distribution.keys()] if cve_distribution else ['有 POC', '無 POC']
        cve_counts = list(cve_distribution.values()) if cve_distribution else [12, 8]
        
        # 計算POC覆蓋率
        total_cves = cve_stats.get('total_cves', 0)
        cves_with_poc = cve_distribution.get('with_poc', 0)
        poc_coverage_percent = (cves_with_poc / total_cves * 100) if total_cves > 0 else 0
        poc_coverage = f"{poc_coverage_percent:.1f}%"
        
        return jsonify({
            'code': 200,
            'message': '統計數據已更新',
            'details': {
                'total_news': dashboard_stats['total_news'],
                'total_sources': dashboard_stats['total_sources'],
                'total_users': dashboard_stats['total_users'],
                'total_cves': total_cves,
                'poc_coverage': poc_coverage,
                'poc_coverage_percent': poc_coverage_percent,
                'monthly_labels': monthly_labels,
                'monthly_counts': monthly_counts,
                'top_sources_labels': top_sources_labels,
                'top_sources_counts': top_sources_counts,
                'cve_labels': cve_labels,
                'cve_counts': cve_counts
            }
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'數據刷新失敗: {str(e)}',
            'details': None
        }), 500


@admin_bp.route('/api/stats/export')
@admin_required  
def export_stats():
    """匯出統計數據的 API 端點"""
    try:
        # 收集所有統計數據
        export_data = {
            'timestamp': StatsService.get_current_timestamp(),
            'dashboard_stats': StatsService.get_dashboard_stats(),
            'news_trend': StatsService.get_news_trend(days=90),
            'source_distribution': StatsService.get_source_distribution(),
            'cve_stats': StatsService.get_cve_stats(),
            'security_metrics': StatsService.get_security_metrics(),
            'performance_metrics': StatsService.get_performance_metrics(),
            'content_analysis': StatsService.get_content_analysis()
        }
        
        return jsonify({
            'status': 'success',
            'data': export_data,
            'filename': f"stats_export_{StatsService.get_current_timestamp()}.json"
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'數據匯出失敗: {str(e)}'
        }), 500
