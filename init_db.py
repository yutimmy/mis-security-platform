# 初始化腳本：建立預設 RSS 來源和管理員帳號
import os
import sys
import logging

# 確保能夠匯入 app 模組並使用正確的路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.path_utils import ensure_project_path
from utils.logging_config import configure_logging, get_logger

import bcrypt
from app import create_app
from app.models.db import db
from app.models.schema import User, RssSource
from config import Config


logger = get_logger(__name__)


def init_database():
    """初始化資料庫和預設資料"""
    # 確保使用正確的專案路徑
    ensure_project_path()

    configure_logging()

    app = create_app()

    with app.app_context():
        logger.info("Initializing database")
        
        # 建立資料表
        db.create_all()
        logger.info("Database tables created")
        
        # 建立預設管理員帳號
        admin_user = User.query.filter_by(username=Config.DEFAULT_ADMIN_USERNAME).first()
        if not admin_user:
            if not Config.DEFAULT_ADMIN_PASSWORD:
                logger.warning("DEFAULT_ADMIN_PASSWORD is not set; aborting admin creation")
                return
            
            password_hash = bcrypt.hashpw(Config.DEFAULT_ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            admin_user = User(
                username=Config.DEFAULT_ADMIN_USERNAME,
                email=Config.DEFAULT_ADMIN_EMAIL,
                password_hash=password_hash,
                role='admin',
                is_active=True
            )
            db.session.add(admin_user)
            logger.info("Created default admin user %s", Config.DEFAULT_ADMIN_USERNAME)
        else:
            logger.info("Default admin user already exists")
        
        # 建立預設 RSS 來源
        for rss_config in Config.DEFAULT_RSS_SOURCES:
            existing = RssSource.query.filter_by(link=rss_config['link']).first()
            if not existing:
                rss_source = RssSource(
                    name=rss_config['name'],
                    link=rss_config['link'],
                    source=rss_config['source'],
                    enabled=True
                )
                db.session.add(rss_source)
                logger.info("Added RSS source %s", rss_config['name'])
            else:
                logger.info("RSS source %s already exists", rss_config['name'])
        
        # 提交變更
        try:
            db.session.commit()
            logger.info("Database initialization completed")
        except Exception as e:
            logger.exception("Database initialization failed: %s", e)
            db.session.rollback()


if __name__ == '__main__':
    init_database()
