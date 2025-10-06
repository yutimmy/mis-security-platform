from unittest.mock import MagicMock, patch

from crawlers.sploitus import SploitusClient, search_sploitus_poc


def test_search_sploitus_poc_rejects_invalid_cve():
    assert search_sploitus_poc("INVALID") == []


@patch("crawlers.sploitus.requests.Session")
def test_search_sploitus_poc_parses_links(mock_session):
    html = """
    <html>
        <body>
            <a href="https://github.com/example/exploit">Exploit PoC</a>
            <a href="/exploit/details">More exploits</a>
            <a href="https://github.com/example/exploit">Duplicate</a>
        </body>
    </html>
    """
    mock_response = MagicMock(status_code=200, content=html)
    mock_session.return_value.get.return_value = mock_response

    results = search_sploitus_poc("CVE-2024-12345", max_links=3)

    assert "https://github.com/example/exploit" in results
    assert "https://sploitus.com/exploit/details" in results
    assert len(results) == 2


@patch("crawlers.sploitus.requests.Session")
def test_search_sploitus_poc_returns_search_url_on_http_error(mock_session):
    mock_response = MagicMock(status_code=429, text="too many requests")
    mock_session.return_value.get.return_value = mock_response

    results = search_sploitus_poc("CVE-2024-12345")

    assert results == ["https://sploitus.com/?query=CVE-2024-12345"]


@patch("crawlers.sploitus.search_sploitus_poc")
def test_sploitus_client_batch_search_respects_delay(mock_search):
    mock_search.side_effect = [["link-1"], ["link-2"]]

    client = SploitusClient(rate_limit_delay=0)
    results = client.batch_search(["CVE-1", "CVE-2"])

    assert results == {"CVE-1": ["link-1"], "CVE-2": ["link-2"]}
    assert mock_search.call_count == 2
