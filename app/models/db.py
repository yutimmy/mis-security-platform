# SQLAlchemy 初始化與 BaseModel
import os

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def init_db(app):
    uri = app.config.get("SQLALCHEMY_DATABASE_URI")
    if not uri:
        sqlite_path = app.config.get("SQLITE_PATH", "./data/app.db")
        uri = f"sqlite:///{sqlite_path}"
        app.config["SQLALCHEMY_DATABASE_URI"] = uri

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    if uri.startswith("sqlite:///"):
        db_path = uri.replace("sqlite:///", "", 1)
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    with app.app_context():
        db.create_all()
