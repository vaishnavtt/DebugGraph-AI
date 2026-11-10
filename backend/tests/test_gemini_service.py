"""
Unit tests for GeminiService and Google GenAI SDK integration.
Tests initialization, error handling, structured JSON parsing, timeouts, and rate limits.
All external LLM calls are mocked.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from google.genai import errors as genai_errors
from google.genai import types

from app.core.errors import (
    GeminiAPIError,
    GeminiConfigurationError,
    GeminiInvalidResponseError,
    GeminiRateLimitError,
    GeminiTimeoutError,
)
from app.services.gemini_service import GeminiService


def test_gemini_service_initialization_defaults():
    """Verify GeminiService initializes with configurable defaults."""
    service = GeminiService(api_key="mock_key", model="gemini-flash-latest")
    assert service._api_key == "mock_key"
    assert service.model_name == "gemini-flash-latest"
    assert service.timeout_seconds > 0


def test_gemini_service_missing_api_key_raises_configuration_error():
    """Ensure missing API key raises GeminiConfigurationError."""
    service = GeminiService(api_key=None, client=None)
    # Explicitly clear internal key
    service._api_key = None
    with pytest.raises(GeminiConfigurationError) as exc_info:
        service._get_client()
    assert "not configured" in exc_info.value.message.lower()


def test_gemini_service_placeholder_api_key_raises_configuration_error():
    """Ensure placeholder API key is rejected."""
    service = GeminiService(api_key="your_gemini_api_key_here", client=None)
    with pytest.raises(GeminiConfigurationError) as exc_info:
        service._get_client()
    assert "placeholder" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_gemini_generate_json_success():
    """Verify successful generation parses JSON and returns token metadata."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"incident_summary": "Database connection pool exhausted", "severity": "HIGH"}'
    mock_response.usage_metadata.prompt_token_count = 120
    mock_response.usage_metadata.candidates_token_count = 45
    mock_response.usage_metadata.total_token_count = 165

    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    service = GeminiService(api_key="mock_valid_key", client=mock_client)
    result = await service.generate_json(
        contents="Analyze logs",
        system_instruction="Strict grounding",
    )

    assert result["data"]["incident_summary"] == "Database connection pool exhausted"
    assert result["data"]["severity"] == "HIGH"
    assert result["prompt_tokens"] == 120
    assert result["completion_tokens"] == 45
    assert result["total_tokens"] == 165
    assert result["latency_ms"] >= 0.0
    assert result["model_name"] in ["gemini-flash-latest", service.model_name]


@pytest.mark.asyncio
async def test_gemini_generate_json_empty_text_raises_invalid_response():
    """Verify empty text response raises GeminiInvalidResponseError."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = ""

    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    service = GeminiService(api_key="mock_valid_key", client=mock_client)
    with pytest.raises(GeminiInvalidResponseError) as exc_info:
        await service.generate_json(contents="Analyze logs")
    assert "empty" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_gemini_generate_json_malformed_json_raises_invalid_response():
    """Verify malformed JSON raises GeminiInvalidResponseError."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "NOT_A_VALID_JSON {summary: broken"

    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    service = GeminiService(api_key="mock_valid_key", client=mock_client)
    with pytest.raises(GeminiInvalidResponseError) as exc_info:
        await service.generate_json(contents="Analyze logs")
    assert "json" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_gemini_timeout_raises_timeout_error():
    """Verify asyncio timeout raises GeminiTimeoutError."""
    mock_client = MagicMock()

    async def slow_generation(*args, **kwargs):
        await asyncio.sleep(2.0)
        return MagicMock()

    mock_client.aio.models.generate_content = slow_generation

    service = GeminiService(api_key="mock_valid_key", client=mock_client, timeout_seconds=0.05)
    with pytest.raises(GeminiTimeoutError) as exc_info:
        await service.generate_json(contents="Analyze logs")
    assert "timed out" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_gemini_rate_limit_raises_rate_limit_error():
    """Verify 429 quota exhaustion raises GeminiRateLimitError."""
    mock_client = MagicMock()
    api_err = genai_errors.APIError(429, {"error": {"message": "Quota exceeded for quota metric 'Queries'"}})
    mock_client.aio.models.generate_content = AsyncMock(side_effect=api_err)

    service = GeminiService(api_key="mock_valid_key", client=mock_client)
    with pytest.raises(GeminiRateLimitError) as exc_info:
        await service.generate_json(contents="Analyze logs")
    assert "quota" in exc_info.value.message.lower() or "rate" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_gemini_auth_failure_raises_configuration_error():
    """Verify 401 / 403 API keys error raises GeminiConfigurationError."""
    mock_client = MagicMock()
    api_err = genai_errors.APIError(403, {"error": {"message": "API_KEY_INVALID"}})
    mock_client.aio.models.generate_content = AsyncMock(side_effect=api_err)

    service = GeminiService(api_key="mock_valid_key", client=mock_client)
    with pytest.raises(GeminiConfigurationError) as exc_info:
        await service.generate_json(contents="Analyze logs")
    assert "authentication" in exc_info.value.message.lower() or "invalid" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_gemini_upstream_server_error_raises_api_error():
    """Verify upstream 500 server error raises GeminiAPIError."""
    mock_client = MagicMock()
    api_err = genai_errors.APIError(500, {"error": {"message": "Internal server error in Gemini service"}})
    mock_client.aio.models.generate_content = AsyncMock(side_effect=api_err)

    service = GeminiService(api_key="mock_valid_key", client=mock_client)
    with pytest.raises(GeminiAPIError) as exc_info:
        await service.generate_json(contents="Analyze logs")
    assert "gemini api error" in exc_info.value.message.lower()
