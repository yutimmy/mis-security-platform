import os
import sys
from pathlib import Path
from typing import Generator

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DEFAULT_ADMIN_USERNAME", "admin")
os.environ.setdefault("DEFAULT_ADMIN_PASSWORD", "admin123")
os.environ.setdefault("DEFAULT_ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("SQLITE_PATH", str(PROJECT_ROOT / "instance" / "test_app.db"))
os.environ.setdefault("FLASK_ENV", "testing")


def _prepare_database_file() -> None:
    db_path = Path(os.environ["SQLITE_PATH"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()


@pytest.fixture(scope="session")
def app() -> Generator["Flask", None, None]:
    _prepare_database_file()

    from app import create_app
    from app.models.db import db
    import app.models.schema  # noqa: F401  # ensure models are registered

    app = create_app()
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SERVER_NAME="localhost",
    )

    with app.app_context():
        db.drop_all()
        db.create_all()
        _seed_defaults()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db_session(app):
    from app.models.db import db

    with app.app_context():
        try:
            yield db.session
        finally:
            db.session.rollback()


@pytest.fixture()
def test_user(app) -> int:
    from app.models.db import db
    from app.models.schema import User

    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        if user is None:
            user = User(
                username="testuser",
                email="testuser@example.com",
                password_hash="test-hash",
                role="user",
                is_active=True,
            )
            db.session.add(user)
            db.session.commit()
        return user.id


@pytest.fixture()
def admin_user(app):
    from app.models.schema import User

    with app.app_context():
        return User.query.filter_by(username=os.environ["DEFAULT_ADMIN_USERNAME"]).first()


@pytest.fixture()
def authenticated_client(app, client, test_user):
    with client.session_transaction() as session:
        session["user_id"] = test_user
    return client


def _seed_defaults() -> None:
    from hashlib import sha256

    from app.models.db import db
    from app.models.schema import RssSource, User

    admin_username = os.environ["DEFAULT_ADMIN_USERNAME"]
    admin = User.query.filter_by(username=admin_username).first()

    if admin is None:
        password = os.environ["DEFAULT_ADMIN_PASSWORD"].encode()
        password_hash = sha256(password).hexdigest()
        admin = User(
            username=admin_username,
            email=os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@example.com"),
            password_hash=password_hash,
            role="admin",
            is_active=True,
        )
        db.session.add(admin)

    if not RssSource.query.count():
        db.session.add(
            RssSource(
                name="Test Source",
                link="https://example.com/rss",
                source="example",
                enabled=True,
            )
        )

    db.session.commit()
