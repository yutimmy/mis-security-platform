# RSS 服務：處理 RSS 爬蟲任務
import json
import logging
from datetime import datetime

from app.models.db import db
from app.models.schema import RssSource, News, JobRun
from config import Config
from crawlers.genai_client import GenAIClient
from crawlers.rss import process_rss_feed, save_items_to_db
from utils.timezone_utils import get_current_time


logger = logging.getLogger(__name__)


def _now():
    """取得當前本地時間"""
    return get_current_time(Config.TIMEZONE)


class RSSService:
    """RSS 爬蟲服務"""
    
    def __init__(self):
        self.config = Config()
        self.genai_client = None
        
        # 初始化 GenAI 客戶端
        if self.config.GOOGLE_GENAI_API_KEY:
            try:
                self.genai_client = GenAIClient()
            except Exception as e:
                logger.warning("GenAI client initialization failed: %s", e)
    
    def run_all_rss(self):
        """執行所有啟用的 RSS 來源"""
        # 記錄任務開始
        job_run = JobRun(
            job_type='rss_all',
            target=None,
            started_at=_now(),
            status='running'
        )
        db.session.add(job_run)
        db.session.commit()
        
        try:
            # 取得所有啟用的 RSS 來源
            rss_sources = RssSource.query.filter_by(enabled=True).all()
            
            if not rss_sources:
                job_run.status = 'failed'
                job_run.ended_at = _now()
                job_run.error_count = 1
                db.session.commit()
                return {
                    'success': False,
                    'message': '沒有啟用的 RSS 來源',
                    'job_run_id': job_run.id
                }
            
            total_processed = 0
            total_new = 0
            total_errors = 0
            total_ai_requests = 0
            total_ai_skipped = 0
            
            for source in rss_sources:
                try:
                    logger.info("Processing RSS source %s", source.name)
                    
                    # 處理 RSS feed
                    result = process_rss_feed(
                        source.link,
                        source.source,
                        self.genai_client,
                        self.config.JINA_MAX_RPM,
                        self.config.JINA_TIMEOUT,
                        self.config.JINA_MAX_RETRIES
                    )
                    
                    # 儲存到資料庫
                    if result['items']:
                        save_stats = save_items_to_db(
                            result['items'], 
                            db.session, 
                            News
                        )
                        
                        total_new += save_stats['inserted']
                        total_new += save_stats.get('updated', 0)  # 更新也計入新增
                        total_errors += save_stats['errors']
                    
                    total_processed += result['processed']
                    total_errors += result['errors']
                    total_ai_requests += result.get('ai_requests', 0)
                    total_ai_skipped += result.get('ai_skipped', 0)
                    
                    # 更新來源最後執行時間
                    source.last_run_at = _now()
                    
                except Exception as e:
                    logger.exception("Error processing RSS source %s", source.name)
                    total_errors += 1
            
            # 更新任務記錄
            job_run.status = 'success' if total_errors == 0 else 'partial'
            job_run.ended_at = _now()
            job_run.inserted_count = total_new
            job_run.error_count = total_errors
            
            db.session.commit()
            
            return {
                'success': True,
                'message': (
                    f'RSS 爬蟲執行完成：處理 {total_processed} 項，新增 {total_new} 項，'
                    f'錯誤 {total_errors} 項，AI 呼叫 {total_ai_requests} 次，跳過 {total_ai_skipped} 次'
                ),
                'job_run_id': job_run.id,
                'stats': {
                    'processed': total_processed,
                    'new_items': total_new,
                    'errors': total_errors,
                    'ai_requests': total_ai_requests,
                    'ai_skipped': total_ai_skipped
                }
            }
            
        except Exception as e:
            logger.exception("Failed to run RSS crawler for all sources")
            job_run.status = 'failed'
            job_run.ended_at = _now()
            job_run.error_count = 1
            db.session.commit()

            return {
                'success': False,
                'message': f'RSS 爬蟲執行失敗：{str(e)}',
                'job_run_id': job_run.id
            }
    
    def run_single_rss(self, rss_id):
        """執行單個 RSS 來源"""
        # 取得 RSS 來源
        source = RssSource.query.get(rss_id)
        if not source:
            return {
                'success': False,
                'message': 'RSS 來源不存在'
            }
        
        # 記錄任務開始
        job_run = JobRun(
            job_type='rss_single',
            target=source.name,
            started_at=_now(),
            status='running'
        )
        db.session.add(job_run)
        db.session.commit()
        
        try:
            logger.info("Processing single RSS source %s", source.name)
            
            # 處理 RSS feed
            result = process_rss_feed(
                source.link,
                source.source,
                self.genai_client,
                self.config.JINA_MAX_RPM,
                self.config.JINA_TIMEOUT,
                self.config.JINA_MAX_RETRIES
            )
            
            # 儲存到資料庫
            new_items = 0
            errors = 0
            ai_requests = result.get('ai_requests', 0)
            ai_skipped = result.get('ai_skipped', 0)
            
            if result['items']:
                save_stats = save_items_to_db(
                    result['items'], 
                    db.session, 
                    News
                )
                new_items = save_stats['inserted']
                new_items += save_stats.get('updated', 0)  # 更新也計入新增
                errors = save_stats['errors']
            
            errors += result['errors']
            
            # 更新來源最後執行時間
            source.last_run_at = _now()
            
            # 更新任務記錄
            job_run.status = 'success' if errors == 0 else 'partial'
            job_run.ended_at = _now()
            job_run.inserted_count = new_items
            job_run.error_count = errors
            
            db.session.commit()
            
            return {
                'success': True,
                'message': (
                    f'RSS 來源 {source.name} 處理完成：處理 {result["processed"]} 項，新增 {new_items} 項，'
                    f'錯誤 {errors} 項，AI 呼叫 {ai_requests} 次，跳過 {ai_skipped} 次'
                ),
                'job_run_id': job_run.id,
                'stats': {
                    'processed': result['processed'],
                    'new_items': new_items,
                    'errors': errors,
                    'ai_requests': ai_requests,
                    'ai_skipped': ai_skipped
                }
            }
            
        except Exception as e:
            logger.exception("Failed to process RSS source %s", source.name)
            job_run.status = 'failed'
            job_run.ended_at = _now()
            job_run.error_count = 1
            db.session.commit()

            return {
                'success': False,
                'message': f'RSS 來源處理失敗：{str(e)}',
                'job_run_id': job_run.id
            }
    
    def rerun_ai_analysis(self, news_id):
        """重新執行 AI 分析"""
        news = News.query.get(news_id)
        if not news:
            return {
                'success': False,
                'message': '新聞不存在'
            }
        
        if not self.genai_client:
            return {
                'success': False,
                'message': 'GenAI 客戶端未設定'
            }
        
        # 記錄任務開始
        job_run = JobRun(
            job_type='ai_rerun',
            target=f'news_{news_id}',
            started_at=_now(),
            status='running'
        )
        db.session.add(job_run)
        db.session.commit()
        
        try:
            # 重新執行 AI 分析
            ai_analysis = self.genai_client.generate_analysis(
                news.content,
                news.title,
                news.source
            )
            
            # 更新新聞記錄
            news.ai_content = json.dumps(ai_analysis, ensure_ascii=False)
            if ai_analysis.get('keywords'):
                news.keyword = ', '.join(ai_analysis['keywords'])
            
            # 更新任務記錄
            job_run.status = 'success'
            job_run.ended_at = _now()
            job_run.inserted_count = 1
            
            db.session.commit()
            
            return {
                'success': True,
                'message': 'AI 分析重新執行完成',
                'job_run_id': job_run.id,
                'ai_analysis': ai_analysis
            }
            
        except Exception as e:
            logger.exception("AI re-analysis failed for news %s", news_id)
            job_run.status = 'failed'
            job_run.ended_at = _now()
            job_run.error_count = 1
            db.session.commit()
            
            return {
                'success': False,
                'message': f'AI 分析重新執行失敗：{str(e)}',
                'job_run_id': job_run.id
            }
