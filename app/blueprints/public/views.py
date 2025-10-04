from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, Optional

from flask import Blueprint, render_template, request
from sqlalchemy import func

from app.models.schema import News, RssSource
from utils.prompt_loader import load_all_prompts


DATE_FORMAT = "%Y-%m-%d"

public_bp = Blueprint('public', __name__)


def _parse_date(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except ValueError:
        return None


def _load_ai_payload(raw: object) -> Dict[str, object]:
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        return {}
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return {}


@public_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    source = request.args.get('source', '').strip()
    search = request.args.get('q', '').strip()
    date_from_str = request.args.get('date_from', '').strip()
    date_to_str = request.args.get('date_to', '').strip()

    query = News.query

    if source:
        query = query.filter(News.source == source)

    if search:
        like_pattern = f"%{search}%"
        query = query.filter(
            News.title.ilike(like_pattern)
            | News.content.ilike(like_pattern)
            | News.cve_id.ilike(like_pattern)
        )

    date_from = _parse_date(date_from_str)
    if date_from:
        query = query.filter(News.created_at >= date_from)

    date_to = _parse_date(date_to_str)
    if date_to:
        query = query.filter(News.created_at < date_to + timedelta(days=1))

    news_list = query.order_by(News.created_at.desc()).paginate(
        page=page,
        per_page=12,
        error_out=False,
    )

    sources = (
        RssSource.query.filter_by(enabled=True)
        .order_by(RssSource.name.asc())
        .all()
    )
    source_lookup = {src.source: src.name for src in sources if src.source}

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)

    total_news = News.query.count()
    news_past_week = News.query.filter(News.created_at >= week_start).count()
    ai_enriched = News.query.filter(
        News.ai_content != None,  # noqa: E711
        News.ai_content != '',
    ).count()
    tracked_sources = News.query.with_entities(News.source).distinct().count()

    stat_cards = [
        {"label": "文章總數", "value": total_news, "caption": "資料庫累積"},
        {"label": "過去 7 天", "value": news_past_week, "caption": "近週新增"},
        {"label": "AI 強化", "value": ai_enriched, "caption": "含 AI 摘要"},
        {"label": "資料來源", "value": tracked_sources, "caption": "活躍來源"},
    ]

    recent_items = News.query.order_by(News.created_at.desc()).limit(80).all()
    cve_counter = Counter()
    for item in recent_items:
        if not item.cve_id:
            continue
        for raw_cve in item.cve_id.split(','):
            cve = raw_cve.strip()
            if cve:
                cve_counter[cve] += 1
    trending_cves = [
        {"cve": cve, "count": count}
        for cve, count in cve_counter.most_common(6)
    ]

    source_counts = (
        News.query.with_entities(News.source, func.count(News.id))
        .group_by(News.source)
        .order_by(func.count(News.id).desc())
        .limit(6)
        .all()
    )
    top_sources = []
    for key, count in source_counts:
        label = source_lookup.get(key, key or "未標記來源")
        top_sources.append({"key": key, "label": label, "count": count})

    ai_candidates = (
        News.query.filter(
            News.ai_content != None,  # noqa: E711
            News.ai_content != '',
        )
        .order_by(News.created_at.desc())
        .limit(4)
        .all()
    )
    ai_highlights = []
    for item in ai_candidates:
        payload = _load_ai_payload(item.ai_content)
        summary = payload.get('summary') or payload.get('summarization')
        if not summary and item.content:
            snippet = item.content.strip()
            summary = snippet[:180] + ('...' if len(snippet) > 180 else '')
        ai_highlights.append(
            {
                "news_id": item.id,
                "title": item.title,
                "summary": summary,
                "created_at": item.created_at,
                "source": source_lookup.get(item.source, item.source or "未分類"),
            }
        )

    prompt_cards = load_all_prompts()[:4]

    filters = {
        "q": search,
        "source": source,
        "date_from": date_from_str,
        "date_to": date_to_str,
    }
    has_filters = any(value for value in filters.values())

    return render_template(
        'public/index.html',
        news_list=news_list,
        sources=sources,
        source_lookup=source_lookup,
        stat_cards=stat_cards,
        trending_cves=trending_cves,
        top_sources=top_sources,
        ai_highlights=ai_highlights,
        prompt_cards=prompt_cards,
        filters=filters,
        has_filters=has_filters,
    )


@public_bp.route('/news/<int:news_id>')
def news_detail(news_id: int):
    news = News.query.get_or_404(news_id)
    ai_content = _load_ai_payload(news.ai_content)

    cve_list = []
    if news.cve_id:
        cve_list = [
            cve.strip()
            for cve in news.cve_id.split(',')
            if cve.strip()
        ]

    return render_template(
        'public/news_detail.html',
        news=news,
        ai_content=ai_content,
        cve_list=cve_list,
    )
