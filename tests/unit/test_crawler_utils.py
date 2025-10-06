from crawlers.cleaners import clean_html_content, normalize_text
from crawlers.extractors import extract_cves, extract_emails


def test_extract_cves_and_emails_are_sorted_and_unique():
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


def test_clean_html_and_normalize_remove_scripts_and_join_lines():
    html_content = (
        "<html><body><h1>Security News</h1><p>This is a <strong>security alert</strong>."
        "</p><script>alert('malicious');</script><style>body { color: red; }</style></body></html>"
    )
    clean_text = clean_html_content(html_content)
    assert "Security News" in clean_text
    assert "security alert" in clean_text
    assert "script" not in clean_text

    messy_text = "Line 1\r\n\n\nLine 2\r\n\n\nLine 3"
    assert normalize_text(messy_text) == "Line 1\n\nLine 2\n\nLine 3"
