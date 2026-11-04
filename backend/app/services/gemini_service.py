"""
Gemini LLM Service for DebugGraph AI.
Provides asynchronous integration with Google's official google-genai SDK,
enforcing structured JSON generation, timeout management, rate-limit resilience,
and credential protection.
"""
import asyncio
import json
import time
from typing import Any, Dict, Optional

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.core.config import settings
from app.core.errors import (
    GeminiAPIError,
    GeminiConfigurationError,
    GeminiInvalidResponseError,
    GeminiRateLimitError,
    GeminiTimeoutError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class GeminiService:
    """
    Reusable service for interacting with Google's Gemini models via google-genai SDK.
    Supports asynchronous execution, structured JSON outputs, and comprehensive error handling.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        client: Optional[Any] = None,
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """
        Initialize GeminiService.

        Parameters:
        - api_key: Gemini API key (defaults to settings.GEMINI_API_KEY).
        - model: Model name (defaults to settings.GEMINI_MODEL or 'gemini-flash-latest').
        - client: Optional pre-configured genai.Client instance (useful for dependency injection and tests).
        - timeout_seconds: Maximum allowed time for request execution.
        """
        self._api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model or settings.GEMINI_MODEL or "gemini-flash-latest"
        self._client = client
        self.timeout_seconds = timeout_seconds or getattr(settings, "GEMINI_TIMEOUT_SECONDS", 30.0)

    def _get_client(self) -> genai.Client:
        """
        Lazily creates or returns the Gemini client.
        Validates API key presence before instantiation.
        """
        if self._client is not None:
            return self._client

        if not self._api_key or self._api_key.strip() in (
            "",
            "your_gemini_api_key_here",
            "your-gemini-api-key-here",
            "placeholder",
        ):
            raise GeminiConfigurationError(
                message="Gemini API key is not configured or contains a placeholder value. "
                "Please configure a valid GEMINI_API_KEY in your environment.",
                details={"configured": bool(self._api_key), "model": self.model_name},
            )

        try:
            self._client = genai.Client(api_key=self._api_key)
            return self._client
        except Exception as exc:
            logger.error("Failed to initialize Gemini Client: %s", exc)
            raise GeminiConfigurationError(
                message=f"Failed to initialize Gemini Client: {str(exc)}",
                details={"model": self.model_name},
            ) from exc

    async def generate_json(
        self,
        contents: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
        timeout_seconds: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Asynchronously generates a structured JSON completion using Gemini.

        Parameters:
        - contents: The primary prompt content containing the incident query and log evidence.
        - system_instruction: System prompt enforcing domain context and evidence grounding.
        - temperature: Sampling temperature (defaults to settings.GEMINI_TEMPERATURE or 0.2).
        - max_output_tokens: Maximum tokens in completion.
        - timeout_seconds: Timeout for this specific generation.

        Returns:
        - Dict with:
            - 'data': Parsed JSON dict from Gemini output
            - 'prompt_tokens': Number of prompt tokens (if available)
            - 'completion_tokens': Number of completion tokens (if available)
            - 'total_tokens': Total tokens consumed (if available)
            - 'latency_ms': Round-trip latency in milliseconds
            - 'model_name': Name of model used
        """
        client = self._get_client()
        effective_timeout = timeout_seconds or self.timeout_seconds
        effective_temperature = (
            temperature if temperature is not None else getattr(settings, "GEMINI_TEMPERATURE", 0.2)
        )
        effective_max_tokens = max_output_tokens or getattr(settings, "GEMINI_MAX_OUTPUT_TOKENS", 4096)

        config = types.GenerateContentConfig(
            temperature=effective_temperature,
            max_output_tokens=effective_max_tokens,
            response_mime_type="application/json",
            system_instruction=system_instruction,
        )

        start_time = time.perf_counter()
        logger.info(
            "Dispatching structured analysis request to Gemini [model=%s, timeout=%.1fs]",
            self.model_name,
            effective_timeout,
        )

        models_to_try = [self.model_name]
        for fallback in ["gemini-3.5-flash-lite", "gemini-3.5-flash"]:
            if fallback not in models_to_try:
                models_to_try.append(fallback)

        response = None
        last_exception = None
        used_model = self.model_name

        for candidate_model in models_to_try:
            used_model = candidate_model
            try:
                # Execute with asyncio timeout protection
                response = await asyncio.wait_for(
                    client.aio.models.generate_content(
                        model=candidate_model,
                        contents=contents,
                        config=config,
                    ),
                    timeout=effective_timeout,
                )
                if response:
                    break
            except asyncio.TimeoutError as exc:
                logger.warning("Gemini generation timed out after %.1f seconds [model=%s]", effective_timeout, candidate_model)
                last_exception = GeminiTimeoutError(
                    message=f"Gemini API request timed out after {effective_timeout} seconds.",
                    details={"model": candidate_model, "timeout_seconds": effective_timeout},
                )
                continue
            except genai_errors.APIError as exc:
                error_code = getattr(exc, "code", None)
                err_msg_lower = exc.message.lower() if exc.message else ""
                logger.warning("Gemini API returned error for model %s: code=%s, message=%s", candidate_model, error_code, exc.message)

                if error_code in (503, 404) or "unavailable" in err_msg_lower or "high demand" in err_msg_lower:
                    last_exception = GeminiAPIError(
                        message=f"Gemini API model {candidate_model} unavailable ({error_code}): {exc.message}",
                        details={"model": candidate_model, "code": error_code},
                    )
                    continue

                if error_code == 429 or "resource_exhausted" in err_msg_lower or "quota" in err_msg_lower or "rate" in err_msg_lower:
                    raise GeminiRateLimitError(
                        message="Gemini API rate limit or quota exceeded. Please retry shortly.",
                        details={"model": candidate_model, "code": error_code},
                    ) from exc
                if error_code in (401, 403) or "permission_denied" in err_msg_lower or "api_key" in err_msg_lower:
                    raise GeminiConfigurationError(
                        message="Gemini API authentication failed. Verify that GEMINI_API_KEY is valid.",
                        details={"model": candidate_model, "code": error_code},
                    ) from exc
                raise GeminiAPIError(
                    message=f"Gemini API error ({error_code}): {exc.message}",
                    details={"model": candidate_model, "code": error_code},
                ) from exc
            except Exception as exc:
                logger.error("Unexpected error communicating with Gemini [model=%s]: %s", candidate_model, exc)
                last_exception = exc
                continue

        if response is None:
            if isinstance(last_exception, (GeminiTimeoutError, GeminiAPIError, GeminiConfigurationError, GeminiRateLimitError)):
                raise last_exception
            raise GeminiAPIError(
                message=f"Unexpected error communicating with Gemini: {str(last_exception)}",
                details={"model": self.model_name, "error_type": type(last_exception).__name__ if last_exception else "Unknown"},
            )

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # Validate that text was returned
        raw_text = getattr(response, "text", None)
        if not raw_text or not raw_text.strip():
            logger.error("Gemini returned empty text response")
            raise GeminiInvalidResponseError(
                message="Gemini returned an empty response.",
                details={"model": self.model_name, "latency_ms": latency_ms},
            )

        # Parse JSON
        try:
            parsed_json = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse Gemini output as JSON: %s", exc)
            raise GeminiInvalidResponseError(
                message="Gemini output could not be parsed as valid JSON.",
                details={"model": self.model_name, "parse_error": str(exc)},
            ) from exc

        # Extract usage metadata safely
        usage_metadata = getattr(response, "usage_metadata", None)
        prompt_tokens = getattr(usage_metadata, "prompt_token_count", None) if usage_metadata else None
        completion_tokens = (
            getattr(usage_metadata, "candidates_token_count", None) if usage_metadata else None
        )
        total_tokens = getattr(usage_metadata, "total_token_count", None) if usage_metadata else None

        logger.info(
            "Gemini response successfully parsed in %.2f ms [prompt_tokens=%s, completion_tokens=%s]",
            latency_ms,
            prompt_tokens,
            completion_tokens,
        )

        return {
            "data": parsed_json,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "latency_ms": round(latency_ms, 2),
            "model_name": used_model,
        }

