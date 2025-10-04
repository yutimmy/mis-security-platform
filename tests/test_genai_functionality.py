"""Unit tests for the GenAI client helpers."""
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from crawlers.genai_client import GenAIClient, RateLimitExceeded
from utils.rate_limiter import RateLimiter


@pytest.fixture(scope="module")
def mock_genai_model():
    with patch("google.generativeai.GenerativeModel") as mock_model:
        yield mock_model


def test_generate_analysis_parses_embedded_json(mock_genai_model):
    response = MagicMock()
    response.text = "Intro text {\n  \"summary\": \"測試摘要\",\n  \"translation\": \"Test translation\",\n  \"how_to_exploit\": \"測試利用說明\",\n  \"keywords\": [\"測試\", \"關鍵字\"]\n}\nFooter"

    instance = MagicMock()
    instance.generate_content.return_value = response
    mock_genai_model.return_value = instance

    client = GenAIClient(api_key="fake-key", model="fake-model")
    result = client.generate_analysis("test text")

    assert result["summary"] == "測試摘要"
    assert result["translation"] == "Test translation"
    assert "測試" in result["keywords"]


def test_generate_analysis_returns_fallback_on_exception(mock_genai_model):
    instance = MagicMock()
    instance.generate_content.side_effect = RuntimeError("api down")
    mock_genai_model.return_value = instance

    client = GenAIClient(api_key="fake-key", model="fake-model")
    result = client.generate_analysis("test text")

    assert result["summary"] == "AI 分析失敗"
    assert result["keywords"] == []


def test_connection_handles_errors(mock_genai_model):
    instance = MagicMock()
    instance.generate_content.side_effect = RuntimeError("api down")
    mock_genai_model.return_value = instance

    client = GenAIClient(api_key="fake-key", model="fake-model")
    success, message = client.test_connection()

    assert success is False
    assert "api down" in message


def test_rate_limiter_blocks_when_budget_consumed():
    limiter = RateLimiter(max_calls=1, period=60)

    assert limiter.try_acquire() is True
    assert limiter.try_acquire() is False
    assert limiter.time_until_available() > 0


def test_generate_analysis_respects_rate_limit(mock_genai_model):
    response = MagicMock()
    response.text = '{"summary":"ok","translation":"","how_to_exploit":"","keywords":[]}'

    instance = MagicMock()
    instance.generate_content.return_value = response
    mock_genai_model.return_value = instance

    client = GenAIClient(api_key="fake-key", model="fake-model", max_rpm=1)

    # first call should pass
    first_result = client.generate_analysis("text", news_title="news")
    assert first_result["summary"] == "ok"

    # second call within the same window should raise
    with pytest.raises(RateLimitExceeded):
        client.generate_analysis("text", news_title="news 2")


@patch.dict(os.environ, {"GOOGLE_GENAI_API_KEY": ""})
def test_missing_api_key_raises_value_error():
    with pytest.raises(ValueError):
        GenAIClient(api_key=None)
