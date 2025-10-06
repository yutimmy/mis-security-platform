from types import SimpleNamespace
from unittest.mock import patch

from app.services.ai_service import AIService
from app.services.poc_service import POCService
from app.services.rss_service import RSSService
from app.models.schema import News
from crawlers.rss import process_rss_feed, save_items_to_db


def test_service_initialization_without_api_key(app):
    with app.app_context():
        rss_service = RSSService()
        poc_service = POCService()
        ai_service = AIService()

        assert isinstance(rss_service, RSSService)
        assert isinstance(poc_service, POCService)
        assert isinstance(ai_service, AIService)


@patch("crawlers.rss.feedparser.parse")
def test_process_rss_feed_returns_clean_items(mock_parse):
    entry = SimpleNamespace(
        title="Security update",
        link="https://example.com/item",
        summary="Important advisory mentioning CVE-2024-12345 and contact security@example.com"
    )
    mock_parse.return_value = SimpleNamespace(entries=[entry], bozo=False)

    result = process_rss_feed("https://example.com/rss", "example")

    assert result["processed"] == 1
    assert result["new_items"] == 1
    item = result["items"][0]
    assert item["cve_list"] == ["CVE-2024-12345"]
    assert item["email_list"] == ["security@example.com"]


def test_save_items_to_db_inserts_and_skips_duplicates(app, db_session):
    items = [
        {
            "title": "Security update",
            "link": "https://example.com/item",
            "source": "example",
            "content": "content",
            "ai_analysis": None,
            "cve_list": ["CVE-2024-12345"],
            "email_list": [],
        }
    ]

    with app.app_context():
        stats = save_items_to_db(items, db_session, News)
        assert stats["inserted"] == 1
        assert stats["skipped"] == 0

        stats_again = save_items_to_db(items, db_session, News)
        assert stats_again["inserted"] == 0
        assert stats_again["skipped"] == 1
