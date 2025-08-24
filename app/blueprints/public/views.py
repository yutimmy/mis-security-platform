# 公開頁面：新聞列表、詳情、搜尋
from flask import Blueprint, render_template, request

from app.models.schema import News, RssSource


public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def index():
    """首頁/新聞列表"""
    # TODO: 實作分頁、篩選、搜尋
    page = request.args.get('page', 1, type=int)
    source = request.args.get('source', '')
    search = request.args.get('q', '')
    
    query = News.query
    
    if source:
        query = query.filter(News.source == source)
    
    if search:
        query = query.filter(
            News.title.contains(search) | 
            News.content.contains(search) |
            News.cve_id.contains(search)
        )
    
    news_list = query.order_by(News.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # 取得所有來源供篩選
    sources = RssSource.query.filter_by(enabled=True).all()
    
    return render_template('public/index.html', 
                         news_list=news_list, 
                         sources=sources,
                         current_source=source,
                         search_query=search)


@public_bp.route('/news/<int:news_id>')
def news_detail(news_id):
    """新聞詳情頁"""
    news = News.query.get_or_404(news_id)
    
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
    
    return render_template('public/news_detail.html', 
                         news=news, 
                         ai_content=ai_content,
                         cve_list=cve_list)
