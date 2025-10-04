"""Basic smoke tests for shared crawler utilities."""
import os
import sys

import pytest
from unittest.mock import patch

# Ensure project root is on the path when tests are executed directly
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from crawlers.cleaners import clean_html_content, normalize_text
from crawlers.extractors import extract_cves, extract_emails


def test_extractors_return_sorted_unique_results():
    text = (
        "This vulnerability affects CVE-2024-12345 and CVE-2023-56789."
        " Another issue is cve-2024-99999 which is critical."
    )
    expected_cves = [
        "CVE-2023-56789",
        "CVE-2024-12345",
        "CVE-2024-99999",
    ]
    assert extract_cves(text) == expected_cves

    email_text = (
        "Contact us at security@example.com or admin@test.org for more information."
        " Invalid email: not_an_email@"
    )
    expected_emails = ["admin@test.org", "security@example.com"]
    assert extract_emails(email_text) == expected_emails


def test_clean_html_and_normalization():
    html_content = (
        "<html><body><h1>Security News</h1><p>This is a <strong>security alert</strong>."\
        "</p><script>alert('malicious');</script><style>body { color: red; }</style></body></html>"
    )
    clean_text = clean_html_content(html_content)
    assert "Security News" in clean_text
    assert "security alert" in clean_text
    assert "script" not in clean_text

    messy_text = "Line 1\r\n\n\nLine 2\r\n\n\nLine 3"
    assert normalize_text(messy_text) == "Line 1\n\nLine 2\n\nLine 3"


def test_jina_reader_is_callable():
    from crawlers.jina_reader import fetch_readable

    assert callable(fetch_readable)


@patch.dict(os.environ, {"GOOGLE_GENAI_API_KEY": ""})
def test_genai_client_requires_api_key():
    from crawlers.genai_client import GenAIClient

    with pytest.raises(ValueError):
        GenAIClient(api_key=None)


def test_database_models_queryable():
    from app import create_app
    from app.models.schema import News, RssSource, User

    app = create_app()

    with app.app_context():
        assert User.query.count() >= 0
        assert News.query.count() >= 0
        assert RssSource.query.count() >= 0


def test_sploitus_rejects_invalid_cve():
    from crawlers.sploitus import search_sploitus_poc

    assert search_sploitus_poc("INVALID") == []
