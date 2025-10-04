# POC 查詢服務：處理 Sploitus POC 查詢
import json
import logging
from datetime import datetime

from app.models.db import db
from app.models.schema import News, JobRun, CvePoc
from crawlers.sploitus import SploitusClient


logger = logging.getLogger(__name__)


class POCService:
    """POC 查詢服務"""
    
    def __init__(self):
        self.sploitus_client = SploitusClient()
    
    def search_poc_for_news(self, news_id, cve_ids=None):
        """為新聞搜尋 POC"""
        news = News.query.get(news_id)
        if not news:
            return {
                'success': False,
                'message': '新聞不存在'
            }
        
        # 如果沒有指定 CVE，使用新聞中的所有 CVE
        if not cve_ids:
            if not news.cve_id:
                return {
                    'success': False,
                    'message': '此新聞沒有關聯的 CVE'
                }
            cve_ids = [cve.strip() for cve in news.cve_id.split(',') if cve.strip()]
        
        if not cve_ids:
            return {
                'success': False,
                'message': '沒有可查詢的 CVE'
            }
        
        # 記錄任務開始
        job_run = JobRun(
            job_type='poc_search',
            target=f'news_{news_id}',
            started_at=datetime.now(),
            status='running'
        )
        db.session.add(job_run)
        db.session.commit()
        
        try:
            found_pocs = []
            not_found_cves = []
            error_details = []
            
            for cve_id in cve_ids:
                try:
                    # 檢查是否已有 POC 記錄
                    existing_poc = CvePoc.query.filter_by(cve_id=cve_id).first()
                    if existing_poc:
                        found_pocs.append({
                            'cve_id': cve_id,
                            'links': [existing_poc.poc_link],
                            'source': existing_poc.source,
                            'cached': True
                        })
                        continue
                    
                    # 搜尋 POC
                    logger.info("Searching POC for %s", cve_id)
                    poc_links = self.sploitus_client.search_poc(cve_id)
                    
                    if poc_links:
                        # 儲存找到的 POC
                        for link in poc_links:
                            poc_record = CvePoc(
                                cve_id=cve_id,
                                poc_link=link,
                                source='sploitus',
                                found_at=datetime.now()
                            )
                            
                            # 檢查是否已存在相同的記錄
                            existing = CvePoc.query.filter_by(
                                cve_id=cve_id,
                                poc_link=link
                            ).first()
                            
                            if not existing:
                                db.session.add(poc_record)
                        
                        found_pocs.append({
                            'cve_id': cve_id,
                            'links': poc_links,
                            'source': 'sploitus',
                            'cached': False
                        })
                        logger.info("Found %s POC links for %s", len(poc_links), cve_id)
                    else:
                        not_found_cves.append(cve_id)
                        logger.info("No POC found for %s", cve_id)
                
                except Exception as e:
                    error_msg = f"Error searching POC for {cve_id}: {str(e)}"
                    logger.exception("Error searching POC for %s", cve_id)
                    error_details.append(error_msg)
                    not_found_cves.append(cve_id)
            
            # 更新新聞的 POC 連結
            updated_news = False
            if found_pocs:
                # 取得第一個找到的 POC 連結作為主要連結
                primary_poc = found_pocs[0]['links'][0] if found_pocs[0]['links'] else None
                if primary_poc and not news.poc_link:
                    news.poc_link = primary_poc
                    updated_news = True
            
            # 更新任務記錄
            status = 'success'
            if len(not_found_cves) == len(cve_ids):
                status = 'failed' 
            elif len(not_found_cves) > 0:
                status = 'partial'
                
            job_run.status = status
            job_run.ended_at = datetime.now()
            job_run.inserted_count = len(found_pocs)
            job_run.error_count = len(not_found_cves)
            job_run.skipped_count = 0
            
            # 添加詳細信息到job記錄
            details = {
                'searched_cves': cve_ids,
                'found_pocs': len(found_pocs),
                'not_found': len(not_found_cves),
                'errors': error_details if error_details else None
            }
            job_run.details = json.dumps(details, ensure_ascii=False)
            
            db.session.commit()
            
            # 根據結果生成適當的消息
            if status == 'success':
                message = f'POC 查詢成功完成：找到 {len(found_pocs)} 個 CVE 的 POC'
            elif status == 'partial':
                message = f'POC 查詢部分成功：找到 {len(found_pocs)} 個 CVE 的 POC，{len(not_found_cves)} 個未找到'
            else:
                message = f'POC 查詢未找到任何結果：{len(not_found_cves)} 個 CVE 均未找到 POC'
            
            return {
                'success': True,
                'message': message,
                'job_run_id': job_run.id,
                'found': found_pocs,
                'not_found': not_found_cves,
                'updated_news': updated_news,
                'status': status
            }
            
        except Exception as e:
            error_msg = f'POC 查詢失敗：{str(e)}'
            logger.exception("POC search failed for news %s", news_id)
            
            job_run.status = 'failed'
            job_run.ended_at = datetime.now()
            job_run.error_count = len(cve_ids)
            job_run.details = json.dumps({
                'error': error_msg,
                'searched_cves': cve_ids
            }, ensure_ascii=False)
            db.session.commit()
            
            return {
                'success': False,
                'message': error_msg,
                'job_run_id': job_run.id
            }
    
    def search_poc_for_cve(self, cve_id):
        """為單個 CVE 搜尋 POC"""
        # 檢查是否已有記錄
        existing_pocs = CvePoc.query.filter_by(cve_id=cve_id).all()
        if existing_pocs:
            return {
                'success': True,
                'message': '從快取中取得 POC',
                'cve_id': cve_id,
                'links': [poc.poc_link for poc in existing_pocs],
                'cached': True
            }
        
        try:
            # 搜尋 POC
            poc_links = self.sploitus_client.search_poc(cve_id)
            
            if poc_links:
                # 儲存找到的 POC
                for link in poc_links:
                    poc_record = CvePoc(
                        cve_id=cve_id,
                        poc_link=link,
                        source='sploitus',
                        found_at=datetime.now()
                    )
                    db.session.add(poc_record)
                
                db.session.commit()
                
                return {
                    'success': True,
                    'message': f'為 {cve_id} 找到 {len(poc_links)} 個 POC',
                    'cve_id': cve_id,
                    'links': poc_links,
                    'cached': False
                }
            else:
                return {
                    'success': True,
                    'message': f'{cve_id} 未找到 POC',
                    'cve_id': cve_id,
                    'links': [],
                    'cached': False
                }
                
        except Exception as e:
            logger.exception("POC search failed for %s", cve_id)
            return {
                'success': False,
                'message': f'POC 查詢失敗：{str(e)}',
                'cve_id': cve_id
            }
    
    def get_poc_stats(self):
        """取得 POC 統計資訊"""
        try:
            total_cves = db.session.query(CvePoc.cve_id).distinct().count()
            total_pocs = CvePoc.query.count()
            
            # 取得最近的 POC 記錄
            recent_pocs = CvePoc.query.order_by(
                CvePoc.found_at.desc()
            ).limit(10).all()
            
            return {
                'total_cves': total_cves,
                'total_pocs': total_pocs,
                'recent_pocs': [
                    {
                        'cve_id': poc.cve_id,
                        'poc_link': poc.poc_link,
                        'source': poc.source,
                        'found_at': poc.found_at.strftime('%Y-%m-%d %H:%M') if poc.found_at else None
                    }
                    for poc in recent_pocs
                ]
            }
            
        except Exception as e:
            return {
                'error': str(e)
            }
