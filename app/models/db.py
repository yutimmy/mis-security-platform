# SQLAlchemy 初始化與 BaseModel
import os

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def init_db(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{app.config['SQLITE_PATH']}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    
    # 確保資料夾存在
    db_path = app.config['SQLITE_PATH']
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    with app.app_context():
        db.create_all()
