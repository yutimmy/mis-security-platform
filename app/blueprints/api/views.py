# API 端點：JSON 回應
import json
import logging
from datetime import datetime
from typing import Dict, Optional

from flask import Blueprint, current_app, jsonify, request, session

from app.models.db import db
from app.models.schema import News, JobRun
from app.services.rss_service import RSSService
from app.services.poc_service import POCService
from config import Config
from utils.rate_limiter import RateLimiter
from utils.timezone_utils import get_current_time


logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__)

_GLOBAL_JOB_LIMITERS: Dict[str, RateLimiter] = {}
_POC_LIMITERS: Dict[int, RateLimiter] = {}


def _now():
    """取得當前本地時間"""
    return get_current_time(Config.TIMEZONE)


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
    auth_error = _require_admin()
    if auth_error:
        return auth_error

    limiter = _get_global_job_limiter('rss')
    if limiter and not limiter.try_acquire():
        current_app.logger.warning("RSS job call throttled for user %s", session.get('user_id'))
        return api_response(429, "RSS 爬蟲請求過於頻繁，請稍後再試")
    
    try:
        # 嘗試從 JSON 或 form 或 args 取得資料
        rss_id = None
        if request.is_json:
            data = request.get_json(silent=True) or {}
            rss_id = data.get('rss_id')
        elif request.form:
            rss_id = request.form.get('rss_id')
        elif request.args:
            rss_id = request.args.get('rss_id')
        
        rss_service = RSSService()
        
        if rss_id:
            # 執行單個 RSS 來源
            result = rss_service.run_single_rss(rss_id)
        else:
            # 執行所有 RSS 來源
            result = rss_service.run_all_rss()

        _record_job_trigger(result.get('job_run_id'), session.get('user_id'), session.get('username'))
        
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
        logger.exception("RSS crawl job failed")
        return api_response(500, f"執行RSS爬蟲時發生錯誤：{str(e)}")


@api_bp.route('/jobs/ai', methods=['POST'])
def trigger_ai_analysis():
    """觸發 AI 分析（批次處理沒有 AI 內容的新聞）"""
    auth_error = _require_admin()
    if auth_error:
        return auth_error

    limiter = _get_global_job_limiter('ai_batch')
    if limiter and not limiter.try_acquire():
        current_app.logger.warning("AI batch job throttled for user %s", session.get('user_id'))
        return api_response(429, "AI 分析請求過於頻繁，請稍後再試")
    
    try:
        from datetime import datetime
        from app.models.schema import News
        from app.services.rss_service import RSSService
        
        # 記錄任務開始
        job_run = JobRun(
            job_type='ai_analysis',
            target='all',
            started_at=_now(),
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
            job_run.ended_at = _now()
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
        job_run.ended_at = _now()
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
            job_run.ended_at = _now()
            job_run.error_count = 1
            db.session.commit()
        return api_response(500, f"執行AI分析時發生錯誤：{str(e)}", {"error": error_detail})
    finally:
        if 'job_run' in locals():
            _record_job_trigger(job_run.id, session.get('user_id'), session.get('username'))


@api_bp.route('/jobs/ai-rerun', methods=['POST'])
def trigger_ai_rerun():
    """重新執行 AI 分析"""
    auth_error = _require_admin()
    if auth_error:
        return auth_error

    limiter = _get_global_job_limiter('ai_single')
    if limiter and not limiter.try_acquire():
        current_app.logger.warning("AI rerun throttled for user %s", session.get('user_id'))
        return api_response(429, "AI 重新分析請求過於頻繁，請稍後再試")
    
    data = request.get_json()
    if not data or 'news_id' not in data:
        return api_response(400, "缺少 news_id")
    
    try:
        rss_service = RSSService()
        result = rss_service.rerun_ai_analysis(data['news_id'])
        
        if result['success']:
            _record_job_trigger(result.get('job_run_id'), session.get('user_id'), session.get('username'))
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

    limiter = _get_poc_limiter(session['user_id'])
    if limiter and not limiter.try_acquire():
        current_app.logger.info("POC search throttled for user %s", session['user_id'])
        return api_response(429, "POC 查詢頻率過高，請稍後再試")

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
            _record_job_trigger(result.get('job_run_id'), session.get('user_id'), session.get('username'))
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


def _require_admin():
    if 'user_id' not in session:
        return api_response(401, "需要登入")
    if session.get('role') != 'admin':
        return api_response(403, "需要管理員權限")
    return None


def _get_global_job_limiter(name: str) -> Optional[RateLimiter]:
    limit = current_app.config.get('JOB_TRIGGER_MAX_PER_MINUTE', 0)
    if limit <= 0:
        return None
    limiter = _GLOBAL_JOB_LIMITERS.get(name)
    if limiter is None or limiter.max_calls != limit:
        limiter = RateLimiter(limit, 60.0)
        _GLOBAL_JOB_LIMITERS[name] = limiter
    return limiter


def _get_poc_limiter(user_id: int) -> Optional[RateLimiter]:
    limit = current_app.config.get('POC_TRIGGER_MAX_PER_MINUTE', 0)
    if limit <= 0:
        return None
    limiter = _POC_LIMITERS.get(user_id)
    if limiter is None or limiter.max_calls != limit:
        limiter = RateLimiter(limit, 60.0)
        _POC_LIMITERS[user_id] = limiter
    return limiter


def _record_job_trigger(job_run_id: Optional[int], user_id: Optional[int], username: Optional[str]) -> None:
    if not job_run_id or not user_id:
        return

    try:
        job = JobRun.query.get(job_run_id)
        if not job:
            return

        payload: Dict[str, object]
        if job.details:
            try:
                parsed = json.loads(job.details)
                payload = parsed if isinstance(parsed, dict) else {'details': parsed}
            except (ValueError, TypeError):
                payload = {'details': job.details}
        else:
            payload = {}

        payload['triggered_by'] = {
            'user_id': user_id,
            'username': username,
            'at': _now().isoformat()  # UTC timestamp for auditing
        }

        job.details = json.dumps(payload, ensure_ascii=False)
        db.session.commit()
    except Exception as exc:
        current_app.logger.warning('Failed to record job trigger metadata: %s', exc)


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
                'timestamp': _now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'統計數據獲取失敗: {str(e)}',
            'data': None
        }), 500
