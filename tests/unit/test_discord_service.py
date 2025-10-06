from unittest.mock import MagicMock, patch

import pytest

from app.services.notify.discord import DiscordService
from app.models.schema import Notification


@pytest.fixture()
def configured_app(app):
    with app.app_context():
        app.config.update(
            DISCORD_BOT_TOKEN="token",
            DISCORD_CHANNEL_ID="channel",
        )
        yield app


def test_send_notification_returns_false_when_missing_config(app):
    with app.app_context():
        app.config.update(DISCORD_BOT_TOKEN="", DISCORD_CHANNEL_ID="")
        service = DiscordService()
        assert service.send_notification("hello") is False


@patch("app.services.notify.discord.requests.post")
def test_send_notification_success_logs_record(mock_post, configured_app, db_session):
    mock_response = MagicMock(status_code=200)
    mock_post.return_value = mock_response

    with configured_app.app_context():
        service = DiscordService()
        result = service.send_notification("hello world")

        assert result is True
        saved = Notification.query.filter_by(status="sent").all()
        assert len(saved) == 1
        assert saved[0].payload == "hello world"


@patch("app.services.notify.discord.requests.post")
def test_send_notification_failure_records_failure(mock_post, configured_app, db_session):
    mock_response = MagicMock(status_code=500, text="error")
    mock_post.return_value = mock_response

    with configured_app.app_context():
        service = DiscordService()
        result = service.send_notification("oops")

        assert result is False
        record = Notification.query.filter_by(status="failed").first()
        assert record is not None
        assert record.payload == "oops"
