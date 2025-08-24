# 資料表定義
from datetime import datetime

from .db import db


class User(db.Model):
    """使用者表"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin/user/other
    is_active = db.Column(db.Boolean, default=False)  # 註冊後需管理員核可
    discord_user_id = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.Date, default=datetime.utcnow)
    updated_at = db.Column(db.Date, default=datetime.utcnow, onupdate=datetime.utcnow)


class RssSource(db.Model):
    """RSS 來源表"""
    __tablename__ = 'rss_sources'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 顯示名
    link = db.Column(db.String(500), unique=True, nullable=False)  # RSS URL
    source = db.Column(db.String(50), nullable=False)  # 來源識別
    category = db.Column(db.String(50), default='other')  # 新增分類欄位
    description = db.Column(db.Text, nullable=True)  # 新增描述欄位
    enabled = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)  # 新增 is_active 欄位（與 admin 視圖一致）
    last_run_at = db.Column(db.Date, nullable=True)


class News(db.Model):
    """新聞表"""
    __tablename__ = 'news'
    
    id = db.Column(db.Integer, primary_key=True)
    link = db.Column(db.String(500), unique=True, nullable=False)  # 去重依據
    title = db.Column(db.Text, nullable=True)
    source = db.Column(db.String(50), nullable=False)
    rss_source_id = db.Column(db.Integer, db.ForeignKey('rss_sources.id'), nullable=True)  # 新增外鍵關聯
    created_at = db.Column(db.Date, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=True)  # 純文字內容
    ai_content = db.Column(db.Text, nullable=True)  # AI 產生內容 (JSON)
    keyword = db.Column(db.Text, nullable=True)  # 關鍵字
    email = db.Column(db.Text, nullable=True)  # 擷取的 Email
    cve_id = db.Column(db.Text, nullable=True)  # 擷取的 CVE
    poc_link = db.Column(db.Text, nullable=True)  # POC 連結
    
    rss_source = db.relationship('RssSource', backref='news_items')


class CvePoc(db.Model):
    """CVE POC 表"""
    __tablename__ = 'cve_pocs'
    
    id = db.Column(db.Integer, primary_key=True)
    cve_id = db.Column(db.String(20), nullable=False)
    poc_link = db.Column(db.String(500), nullable=False)
    source = db.Column(db.String(50), default='sploitus')
    status = db.Column(db.String(20), default='found')  # 新增狀態欄位
    found_at = db.Column(db.Date, default=datetime.utcnow)
    created_at = db.Column(db.Date, default=datetime.utcnow)  # 新增 created_at 欄位
    
    __table_args__ = (db.UniqueConstraint('cve_id', 'poc_link'),)


class JobRun(db.Model):
    """任務執行記錄表"""
    __tablename__ = 'job_runs'
    
    id = db.Column(db.Integer, primary_key=True)
    job_type = db.Column(db.String(50), nullable=False)  # rss_all/rss_one/poc_check
    target = db.Column(db.String(200), nullable=True)  # RSS 名稱或 CVE
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
    inserted_count = db.Column(db.Integer, default=0)
    skipped_count = db.Column(db.Integer, default=0)
    error_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='running')  # success/partial/failed/running
    details = db.Column(db.Text, nullable=True)  # 詳細執行資訊 (JSON)


class Post(db.Model):
    """Markdown 文章表"""
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)  # 統一使用 content 欄位
    category = db.Column(db.String(50), nullable=True)  # 分類欄位
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_published = db.Column(db.Boolean, default=False)
    views = db.Column(db.Integer, default=0)  # 觀看次數
    created_at = db.Column(db.Date, default=datetime.utcnow)
    updated_at = db.Column(db.Date, default=datetime.utcnow, onupdate=datetime.utcnow)
    tags = db.Column(db.String(200), nullable=True)
    
    author = db.relationship('User', backref='posts')


class Image(db.Model):
    """圖片表"""
    __tablename__ = 'images'
    
    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(200), nullable=False)  # 新增原始檔名
    file_path = db.Column(db.String(200), nullable=False)
    mime_type = db.Column(db.String(50), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 新增上傳者
    related_type = db.Column(db.String(20), nullable=True)  # 關聯類型 (post/news)
    related_id = db.Column(db.Integer, nullable=True)  # 關聯 ID
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)  # 保留原有關聯
    created_at = db.Column(db.Date, default=datetime.utcnow)
    
    user = db.relationship('User', backref='images')
    post = db.relationship('Post', backref='images')


class Notification(db.Model):
    """通知表"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), default='discord')
    payload = db.Column(db.Text, nullable=False)  # JSON 字串
    target_role = db.Column(db.String(20), default='all')  # all/user/admin/custom
    news_id = db.Column(db.Integer, db.ForeignKey('news.id'), nullable=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)
    status = db.Column(db.String(20), default='queued')  # queued/sent/failed
    created_at = db.Column(db.Date, default=datetime.utcnow)
    sent_at = db.Column(db.Date, nullable=True)
    
    news = db.relationship('News', backref='notifications')
    post = db.relationship('Post', backref='notifications')


class ApiUsageLog(db.Model):
    """API 使用記錄表"""
    __tablename__ = 'api_usage_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(50), nullable=False)  # google-genai/jina
    model = db.Column(db.String(50), nullable=True)
    latency_ms = db.Column(db.Integer, nullable=True)
    ok = db.Column(db.Boolean, default=True)
    cost = db.Column(db.Float, nullable=True)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
