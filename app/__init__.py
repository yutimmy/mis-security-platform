# 建立 Flask App、載入配置與藍圖
import os

from flask import Flask

from .models.db import init_db


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    init_db(app)

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

    return app
