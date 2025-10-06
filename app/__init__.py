# 建立 Flask App、載入配置與藍圖
import os

from flask import Flask
from flask_wtf.csrf import CSRFProtect, generate_csrf

from .models.db import init_db
from utils.logging_config import configure_logging


csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    _enforce_secret_key(app)

    csrf.init_app(app)
    configure_logging(app)

    init_db(app)

    @app.context_processor
    def inject_csrf_token():
        return {"csrf_token": lambda: generate_csrf()}

    # 在 app context 中 import blueprints 避免循環 import
    with app.app_context():
        from .blueprints.public.views import public_bp
        from .blueprints.auth.views import auth_bp
        from .blueprints.admin.views import admin_bp
        from .blueprints.api.views import api_bp
        from .blueprints.posts.views import posts_bp

        app.register_blueprint(public_bp)
        app.register_blueprint(auth_bp, url_prefix="/auth")
        app.register_blueprint(admin_bp, url_prefix="/admin")
        app.register_blueprint(api_bp, url_prefix="/api")
        app.register_blueprint(posts_bp, url_prefix="/posts")
        
        # API 端點豁免 CSRF 保護（使用 session-based 驗證）
        csrf.exempt(api_bp)

    return app


def _enforce_secret_key(app: Flask) -> None:
    secret = app.config.get("SECRET_KEY")
    if not secret or secret == "dev-key":
        raise RuntimeError("SECRET_KEY 必須設定為非預設值，請更新環境變數或設定檔")
