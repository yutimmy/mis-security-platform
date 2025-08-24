# 初始化腳本：建立預設 RSS 來源和管理員帳號
import os
import sys

# 確保能夠匯入 app 模組並使用正確的路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.path_utils import ensure_project_path

import bcrypt
from app import create_app
from app.models.db import db
from app.models.schema import User, RssSource
from config import Config


def init_database():
    """初始化資料庫和預設資料"""
    # 確保使用正確的專案路徑
    ensure_project_path()
    
    app = create_app()
    
    with app.app_context():
        print("正在初始化資料庫...")
        
        # 建立資料表
        db.create_all()
        print("資料表建立完成")
        
        # 建立預設管理員帳號
        admin_user = User.query.filter_by(username=Config.DEFAULT_ADMIN_USERNAME).first()
        if not admin_user:
            if not Config.DEFAULT_ADMIN_PASSWORD:
                print("警告：未設定預設管理員密碼，請在 .env 檔案中設定 DEFAULT_ADMIN_PASSWORD")
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
            print(f"已建立預設管理員帳號：{Config.DEFAULT_ADMIN_USERNAME}")
        else:
            print("管理員帳號已存在")
        
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
                print(f"已添加 RSS 來源：{rss_config['name']}")
            else:
                print(f"RSS 來源已存在：{rss_config['name']}")
        
        # 提交變更
        try:
            db.session.commit()
            print("初始化完成！")
        except Exception as e:
            print(f"初始化失敗：{e}")
            db.session.rollback()


if __name__ == '__main__':
    init_database()
