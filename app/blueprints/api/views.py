# API 端點：JSON 回應
import logging
from flask import Blueprint, jsonify, request, session
from datetime import datetime

from app.models.db import db
from app.models.schema import News, RssSource, JobRun
from app.services.rss_service import RSSService
from app.services.poc_service import POCService


logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__)


def api_response(code=200, message="success", data=None, details=None):
    """統一 API 回應格式"""
    response = {
        "code": code,
        "message": message
    }
    if data is not None:
        response["data"] = data
    if details is not None:
        response["details"] = details
    return jsonify(response), code


@api_bp.route('/healthz')
def health_check():
    """健康檢查"""
    return api_response(data={"status": "healthy"})


@api_bp.route('/news')
def get_news():
    """取得新聞列表"""
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    source = request.args.get('source', '')
    q = request.args.get('q', '')
    cve = request.args.get('cve', '')
    has_poc = request.args.get('has_poc', '')
    
    # 限制分頁大小
    size = min(size, 100)
    
    query = News.query
    
    if source:
        query = query.filter(News.source == source)
    
    if q:
        query = query.filter(
            News.title.contains(q) | 
            News.content.contains(q)
        )
    
    if cve:
        query = query.filter(News.cve_id.contains(cve))
    
    if has_poc == 'true':
        query = query.filter(News.poc_link.isnot(None))
    elif has_poc == 'false':
        query = query.filter(News.poc_link.is_(None))
    
    result = query.order_by(News.created_at.desc()).paginate(
        page=page, per_page=size, error_out=False
    )
    
    news_list = []
    for news in result.items:
        # 解析 CVE 列表
        cve_list = []
        if news.cve_id:
            cve_list = [cve.strip() for cve in news.cve_id.split(',') if cve.strip()]
        
        news_data = {
            "id": news.id,
            "title": news.title,
            "source": news.source,
            "created_at": news.created_at.strftime("%Y-%m-%d") if news.created_at else None,
            "link": news.link,
            "cve_list": cve_list,
            "has_poc": bool(news.poc_link)
        }
        news_list.append(news_data)
    
    return api_response(data={
        "news": news_list,
        "pagination": {
            "page": result.page,
            "pages": result.pages,
            "per_page": result.per_page,
            "total": result.total,
            "has_next": result.has_next,
            "has_prev": result.has_prev
        }
    })


@api_bp.route('/news/<int:news_id>')
def get_news_detail(news_id):
    """取得新聞詳情"""
    news = News.query.get(news_id)
    if not news:
        return api_response(404, "新聞不存在")
    
    # 解析 AI 內容
    ai_content = {}
    if news.ai_content:
        try:
            import json
            ai_content = json.loads(news.ai_content)
        except:
            pass
    
    # 解析 CVE 列表
    cve_list = []
    if news.cve_id:
        cve_list = [cve.strip() for cve in news.cve_id.split(',') if cve.strip()]
    
    # 解析 Email 列表
    email_list = []
    if news.email:
        email_list = [email.strip() for email in news.email.split(',') if email.strip()]
    
    news_data = {
        "id": news.id,
        "title": news.title,
        "source": news.source,
        "created_at": news.created_at.strftime("%Y-%m-%d") if news.created_at else None,
        "link": news.link,
        "content": news.content,
        "ai_content": ai_content,
        "keyword": news.keyword,
        "cve_list": cve_list,
        "email_list": email_list,
        "poc_link": news.poc_link
    }
    
    return api_response(data=news_data)


@api_bp.route('/jobs/rss', methods=['POST'])
def trigger_rss_crawl():
    """觸發 RSS 爬蟲"""
    # 檢查權限
    if 'user_id' not in session:
        return api_response(401, "需要登入")
    
    if session.get('role') not in ['admin', 'user']:
        return api_response(403, "權限不足")
    
    try:
        # 嘗試從 JSON 或 form 取得資料
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.form.to_dict()
        
        rss_id = data.get('rss_id')
        
        rss_service = RSSService()
        
        if rss_id:
            # 執行單個 RSS 來源
            result = rss_service.run_single_rss(rss_id)
        else:
            # 執行所有 RSS 來源
            result = rss_service.run_all_rss()
        
        if result['success']:
            return api_response(200, result['message'], {
                'job_run_id': result['job_run_id'],
                'stats': result.get('stats', {})
            })
        else:
            return api_response(500, result['message'], {
                'job_run_id': result.get('job_run_id')
            })
            
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return api_response(500, f"執行RSS爬蟲時發生錯誤：{str(e)}", {"error": error_detail})


@api_bp.route('/jobs/ai', methods=['POST'])
def trigger_ai_analysis():
    """觸發 AI 分析（批次處理沒有 AI 內容的新聞）"""
    if 'user_id' not in session:
        return api_response(401, "需要登入")
    
    if session.get('role') not in ['admin', 'user']:
        return api_response(403, "權限不足")
    
    try:
        from datetime import datetime
        from app.models.schema import News
        from app.services.rss_service import RSSService
        
        # 記錄任務開始
        job_run = JobRun(
            job_type='ai_analysis',
            target='all',
            started_at=datetime.now(),
            status='running'
        )
        db.session.add(job_run)
        db.session.commit()
        
        # 找出所有沒有 AI 內容的新聞
        news_list = News.query.filter(
            (News.ai_content == None) | (News.ai_content == '')
        ).limit(100).all()  # 限制一次處理 100 筆
        
        if not news_list:
            job_run.status = 'success'
            job_run.ended_at = datetime.now()
            job_run.inserted_count = 0
            db.session.commit()
            return api_response(200, '沒有需要分析的新聞', {'job_run_id': job_run.id})
        
        rss_service = RSSService()
        success_count = 0
        error_count = 0
        
        # Rate limiter 會自動處理等待，不需要手動延遲
        for news in news_list:
            try:
                result = rss_service.rerun_ai_analysis(news.id)
                if result['success']:
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                logger.exception("AI analysis failed for news %s", news.id)
                error_count += 1
                continue
        
        # 更新任務記錄
        job_run.status = 'success' if error_count == 0 else 'partial'
        job_run.ended_at = datetime.now()
        job_run.inserted_count = success_count
        job_run.error_count = error_count
        db.session.commit()
        
        return api_response(200, f'AI 分析完成：成功 {success_count} 項，失敗 {error_count} 項', {
            'job_run_id': job_run.id,
            'success_count': success_count,
            'error_count': error_count
        })
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        if 'job_run' in locals():
            job_run.status = 'failed'
            job_run.ended_at = datetime.now()
            job_run.error_count = 1
            db.session.commit()
        return api_response(500, f"執行AI分析時發生錯誤：{str(e)}", {"error": error_detail})


@api_bp.route('/jobs/ai-rerun', methods=['POST'])
def trigger_ai_rerun():
    """重新執行 AI 分析"""
    if 'user_id' not in session:
        return api_response(401, "需要登入")
    
    if session.get('role') not in ['admin', 'user']:
        return api_response(403, "權限不足")
    
    data = request.get_json()
    if not data or 'news_id' not in data:
        return api_response(400, "缺少 news_id")
    
    try:
        rss_service = RSSService()
        result = rss_service.rerun_ai_analysis(data['news_id'])
        
        if result['success']:
            return api_response(200, result['message'], {
                'job_run_id': result['job_run_id'],
                'ai_analysis': result.get('ai_analysis', {})
            })
        else:
            return api_response(500, result['message'], {
                'job_run_id': result.get('job_run_id')
            })
            
    except Exception as e:
        return api_response(500, f"重新執行AI分析時發生錯誤：{str(e)}")


@api_bp.route('/jobs/poc', methods=['POST'])
def trigger_poc_search():
    """觸發 POC 查詢"""
    if 'user_id' not in session:
        return api_response(401, "需要登入")
    
    data = request.get_json()
    if not data or 'news_id' not in data:
        return api_response(400, "缺少 news_id")
    
    try:
        news_id = data['news_id']
        cve_ids = data.get('cve_ids', [])
        
        # 檢查新聞是否存在
        news = News.query.get(news_id)
        if not news:
            return api_response(404, "新聞不存在")
        
        poc_service = POCService()
        result = poc_service.search_poc_for_news(news_id, cve_ids)
        
        if result['success']:
            return api_response(200, result['message'], {
                'job_run_id': result['job_run_id'],
                'found': result['found'],
                'not_found': result['not_found'],
                'updated_news': result['updated_news']
            })
        else:
            return api_response(500, result['message'], {
                'job_run_id': result.get('job_run_id')
            })
            
    except Exception as e:
        return api_response(500, f"執行POC查詢時發生錯誤：{str(e)}")


@api_bp.route('/jobs/status/<int:job_run_id>')
def get_job_status(job_run_id):
    """取得任務執行狀態"""
    job = JobRun.query.get(job_run_id)
    if not job:
        return api_response(404, "任務不存在")
    
    job_data = {
        'id': job.id,
        'job_type': job.job_type,
        'target': job.target,
        'status': job.status,
        'started_at': job.started_at.strftime('%Y-%m-%d %H:%M:%S') if job.started_at else None,
        'ended_at': job.ended_at.strftime('%Y-%m-%d %H:%M:%S') if job.ended_at else None,
        'inserted_count': job.inserted_count,
        'skipped_count': job.skipped_count,
        'error_count': job.error_count
    }
    
    return api_response(200, "取得任務狀態成功", job_data)


@api_bp.route('/jobs/<int:job_run_id>')
def get_job_details(job_run_id):
    """取得任務詳細資訊（用於管理後台）"""
    if 'user_id' not in session:
        return api_response(401, "需要登入")
    
    if session.get('role') not in ['admin', 'user']:
        return api_response(403, "權限不足")
    
    job = JobRun.query.get(job_run_id)
    if not job:
        return api_response(404, "任務不存在")
    
    job_data = {
        'id': job.id,
        'job_type': job.job_type,
        'target': job.target,
        'status': job.status,
        'started_at': job.started_at.strftime('%Y-%m-%d %H:%M:%S') if job.started_at else None,
        'ended_at': job.ended_at.strftime('%Y-%m-%d %H:%M:%S') if job.ended_at else None,
        'inserted_count': job.inserted_count or 0,
        'skipped_count': job.skipped_count or 0,
        'error_count': job.error_count or 0,
        'details': getattr(job, 'details', None) or f"任務類型: {job.job_type}\n目標: {job.target or '全部'}\n狀態: {job.status}"
    }
    
    return api_response(200, "取得任務詳情成功", job_data)


@api_bp.route('/stats/latest', methods=['GET'])
def get_latest_stats():
    """取得最新統計數據（用於實時更新）"""
    try:
        from app.services.stats_service import StatsService
        
        # 取得最新統計數據
        dashboard_stats = StatsService.get_dashboard_stats()
        news_trend = StatsService.get_news_trend(days=30)
        source_distribution = StatsService.get_source_distribution()
        cve_stats = StatsService.get_cve_stats()
        user_activity = StatsService.get_user_activity()
        job_stats = StatsService.get_job_statistics()
        category_stats = StatsService.get_category_statistics()
        security_metrics = StatsService.get_security_metrics()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'dashboardStats': dashboard_stats,
                'newsTrend': news_trend,
                'sourceDistribution': source_distribution,
                'cveStats': cve_stats,
                'userActivity': user_activity,
                'jobStats': job_stats,
                'categoryStats': category_stats,
                'securityMetrics': security_metrics,
                'timestamp': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'統計數據獲取失敗: {str(e)}',
            'data': None
        }), 500
