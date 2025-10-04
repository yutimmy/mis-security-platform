# 主腳本：讀 config/DB 的 RSS，節流調度、清洗、入庫
import json
from datetime import datetime
import logging

import feedparser

from .cleaners import clean_html_content, normalize_text
from .extractors import extract_cves, extract_emails
from .genai_client import GenAIClient, RateLimitExceeded
from .jina_reader import fetch_readable


logger = logging.getLogger(__name__)


def process_rss_feed(rss_url, source_name, genai_client=None, jina_rpm=10):
    """
    處理單個 RSS feed
    
    Args:
        rss_url: RSS 網址
        source_name: 來源名稱
        genai_client: GenAI 客戶端實例
        jina_rpm: Jina Reader 每分鐘請求限制
        
    Returns:
        dict: 處理結果統計
    """
    result = {
        'processed': 0,
        'new_items': 0,
        'errors': 0,
        'items': [],
        'ai_requests': 0,
        'ai_skipped': 0
    }
    
    try:
        logger.info("Processing RSS feed %s (%s)", source_name, rss_url)
        
        # 解析 RSS
        feed = feedparser.parse(rss_url)
        
        if feed.bozo:
            logger.warning("RSS feed reported issues: %s", feed.bozo_exception)
        
        for entry in feed.entries:
            try:
                result['processed'] += 1
                
                # 基本資訊
                title = getattr(entry, 'title', '')
                link = getattr(entry, 'link', '')
                published = getattr(entry, 'published', '')
                
                if not link:
                    continue
                
                # 獲取完整內容
                logger.debug("Fetching content for %s", title[:50])
                
                # 嘗試從 entry 獲取內容
                content = ""
                if hasattr(entry, 'content'):
                    content = entry.content[0].value if entry.content else ""
                elif hasattr(entry, 'summary'):
                    content = entry.summary
                
                # 如果沒有內容或內容太短，使用 Jina Reader
                if len(content) < 100:
                    jina_content = fetch_readable(link, jina_rpm)
                    if jina_content:
                        content = jina_content
                
                # 清理內容
                clean_content = clean_html_content(content)
                clean_content = normalize_text(clean_content)
                
                # 擷取資訊
                cve_list = extract_cves(clean_content)
                email_list = extract_emails(clean_content)
                
                # AI 分析
                ai_analysis = None
                if genai_client and clean_content:
                    logger.debug("Running AI analysis for %s", title[:50])
                    try:
                        ai_analysis = genai_client.generate_analysis(
                            clean_content, title, source_name
                        )
                        result['ai_requests'] += 1
                    except RateLimitExceeded:
                        result['ai_skipped'] += 1
                        logger.info(
                            "Skipped AI analysis for %s due to rate limit", title[:50]
                        )

                # 構建結果項目
                item_data = {
                    'title': title,
                    'link': link,
                    'source': source_name,
                    'published': published,
                    'content': clean_content,
                    'cve_list': cve_list,
                    'email_list': email_list,
                    'ai_analysis': ai_analysis
                }
                
                result['items'].append(item_data)
                result['new_items'] += 1
                
                logger.debug("Processed entry %s", title[:50])
                if cve_list:
                    logger.debug("Extracted CVEs: %s", ", ".join(cve_list))

            except Exception as e:
                logger.exception("Error processing RSS entry: %s", e)
                result['errors'] += 1

        logger.info(
            "RSS processing completed: %s processed, %s new items, %s errors",
            result['processed'],
            result['new_items'],
            result['errors'],
        )

    except Exception as e:
        logger.exception("Error processing RSS feed %s: %s", rss_url, e)
        result['errors'] += 1
    
    return result


def save_items_to_db(items, db_session, news_model):
    """
    將處理好的項目儲存到資料庫
    
    Args:
        items: 處理結果項目清單
        db_session: 資料庫 session
        news_model: News 模型類別
        
    Returns:
        dict: 儲存統計
    """
    stats = {
        'inserted': 0,
        'skipped': 0,
        'errors': 0
    }
    
    for item in items:
        try:
            # 檢查是否已存在（以 link 為準）
            existing = news_model.query.filter_by(link=item['link']).first()
            if existing:
                stats['skipped'] += 1
                continue
            
            # 準備資料
            ai_content_json = ""
            if item['ai_analysis']:
                ai_content_json = json.dumps(item['ai_analysis'], ensure_ascii=False)
            
            # 建立新聞記錄
            news = news_model(
                title=item['title'],
                link=item['link'],
                source=item['source'],
                content=item['content'],
                ai_content=ai_content_json,
                keyword=', '.join(item['ai_analysis'].get('keywords', [])) if item['ai_analysis'] else '',
                cve_id=', '.join(item['cve_list']) if item['cve_list'] else None,
                email=', '.join(item['email_list']) if item['email_list'] else None
            )
            
            db_session.add(news)
            stats['inserted'] += 1
            
        except Exception as e:
            logger.exception("Error saving item %s: %s", item.get('link', 'unknown'), e)
            stats['errors'] += 1

    try:
        db_session.commit()
        logger.info(
            "Database save completed: %s inserted, %s skipped, %s errors",
            stats['inserted'],
            stats['skipped'],
            stats['errors'],
        )
    except Exception as e:
        logger.exception("Error committing RSS items to database: %s", e)
        db_session.rollback()
        stats['errors'] += stats['inserted']
        stats['inserted'] = 0
    
    return stats
