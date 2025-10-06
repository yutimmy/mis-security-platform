# 讀取 .env、集中設定與預設值
import os

from dotenv import load_dotenv


class Config:
    load_dotenv()

    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key")
    SQLITE_PATH = os.path.abspath(os.getenv("SQLITE_PATH", "./data/app.db"))
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{SQLITE_PATH}"
    TIMEZONE = os.getenv("TIMEZONE", "Asia/Taipei")

    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
    DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID", "")

    GOOGLE_GENAI_API_KEY = os.getenv("GOOGLE_GENAI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    JINA_MAX_RPM = int(os.getenv("JINA_MAX_RPM", 10))
    JINA_TIMEOUT = int(os.getenv("JINA_TIMEOUT", 30))  # Jina Reader 請求超時（秒）
    JINA_MAX_RETRIES = int(os.getenv("JINA_MAX_RETRIES", 3))  # Jina Reader 最大重試次數
    GENAI_MAX_RPM = int(os.getenv("GENAI_MAX_RPM", 5))

    ALLOWED_IMAGE_TYPES = os.getenv("ALLOWED_IMAGE_TYPES", "image/png,image/jpeg,image/webp")
    MAX_IMAGE_SIZE_MB = float(os.getenv("MAX_IMAGE_SIZE_MB", 1.5))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "static/uploads/images")

    # API 限制
    API_RATE_LIMIT_PER_MINUTE = int(os.getenv("API_RATE_LIMIT_PER_MINUTE", 60))
    JOB_TRIGGER_MAX_PER_MINUTE = int(os.getenv("JOB_TRIGGER_MAX_PER_MINUTE", 2))
    POC_TRIGGER_MAX_PER_MINUTE = int(os.getenv("POC_TRIGGER_MAX_PER_MINUTE", 5))
    
    # 分頁設定
    ITEMS_PER_PAGE = int(os.getenv("ITEMS_PER_PAGE", 20))
    
    # CSRF / Session 安全
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = int(os.getenv("WTF_CSRF_TIME_LIMIT", 3600))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() in {"1", "true", "yes"}

    # 通知設定
    NOTIFICATION_RATE_LIMIT = int(os.getenv("NOTIFICATION_RATE_LIMIT", 10))  # 每分鐘最多通知數
    
    # 安全設定
    SESSION_TIMEOUT_HOURS = int(os.getenv("SESSION_TIMEOUT_HOURS", 24))
    MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", 5))
    
    # 預設管理員設定
    DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
    DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "")

    DATE_FMT = "%Y-%m-%d"

    # RSS 預設清單
    DEFAULT_RSS_SOURCES = [
        {
            "name": "The Hacker News",
            "link": "https://feeds.feedburner.com/TheHackersNews",
            "source": "thehackernews"
        },
        {
            "name": "Krebs on Security",
            "link": "https://krebsonsecurity.com/feed/",
            "source": "krebsonsecurity"
        },
        {
            "name": "Bleeping Computer",
            "link": "https://www.bleepingcomputer.com/feed/",
            "source": "bleepingcomputer"
        },
        {
            "name": "iThome",
            "link": "https://www.ithome.com.tw/rss",
            "source": "ithome"
        }
    ]
