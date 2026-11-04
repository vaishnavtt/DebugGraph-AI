"""
Centralized exception handling for DebugGraph AI.
Enforces consistent JSON error envelopes and prevents disclosure of stack traces and internal secrets.
"""
from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.responses import ErrorResponse

logger = get_logger(__name__)


class AppException(Exception):
    """Base application exception with status code and error classification."""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str = "INTERNAL_ERROR",
        message: str = "An application error occurred.",
        details: Optional[Any] = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


class GeminiError(AppException):
    """Base exception for Gemini service and LLM integration failures."""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str = "GEMINI_ERROR",
        message: str = "Gemini service encountered an error.",
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(status_code=status_code, code=code, message=message, details=details)


class GeminiConfigurationError(GeminiError):
    """Raised when Gemini credentials or required configurations are missing or invalid."""

    def __init__(
        self,
        message: str = "Gemini API key is not configured.",
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="GEMINI_NOT_CONFIGURED",
            message=message,
            details=details,
        )


class GeminiAPIError(GeminiError):
    """Raised when the Gemini API returns an upstream error or network failure."""

    def __init__(
        self,
        message: str = "Failed to communicate with Gemini API.",
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="GEMINI_API_ERROR",
            message=message,
            details=details,
        )


class GeminiRateLimitError(GeminiError):
    """Raised when Gemini API quota or rate limits are reached."""

    def __init__(
        self,
        message: str = "Gemini API rate limit or quota exceeded.",
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="GEMINI_RATE_LIMIT",
            message=message,
            details=details,
        )


class GeminiTimeoutError(GeminiError):
    """Raised when a request to Gemini times out."""

    def __init__(
        self,
        message: str = "Gemini API request timed out.",
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            code="GEMINI_TIMEOUT",
            message=message,
            details=details,
        )


class GeminiInvalidResponseError(GeminiError):
    """Raised when the Gemini API output is malformed or violates required schema."""

    def __init__(
        self,
        message: str = "Gemini API returned an invalid or unparseable response.",
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="GEMINI_INVALID_RESPONSE",
            message=message,
            details=details,
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register centralized exception handlers on the FastAPI application."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            "Application error on %s %s: [%s] %s",
            request.method,
            request.url.path,
            exc.code,
            exc.message,
        )
        error_payload = ErrorResponse(
            error=True,
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload.model_dump(mode="json"),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        code_map: Dict[int, str] = {
            status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
            status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
            status.HTTP_403_FORBIDDEN: "FORBIDDEN",
            status.HTTP_404_NOT_FOUND: "NOT_FOUND",
            status.HTTP_405_METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
            status.HTTP_409_CONFLICT: "CONFLICT",
            413: "CONTENT_TOO_LARGE",
            422: "UNPROCESSABLE_ENTITY",
            status.HTTP_500_INTERNAL_SERVER_ERROR: "INTERNAL_SERVER_ERROR",
            status.HTTP_503_SERVICE_UNAVAILABLE: "SERVICE_UNAVAILABLE",
        }
        code = code_map.get(exc.status_code, f"HTTP_{exc.status_code}")

        logger.info(
            "HTTP %d on %s %s: %s",
            exc.status_code,
            request.method,
            request.url.path,
            exc.detail,
        )

        error_payload = ErrorResponse(
            error=True,
            code=code,
            message=str(exc.detail),
            details=None,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload.model_dump(mode="json"),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.info(
            "Validation error on %s %s: %s",
            request.method,
            request.url.path,
            exc.errors(),
        )

        error_payload = ErrorResponse(
            error=True,
            code="VALIDATION_ERROR",
            message="Request input validation failed.",
            details=exc.errors(),
        )
        return JSONResponse(
            status_code=422,
            content=error_payload.model_dump(mode="json"),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        # Full stack trace logged internally on the server
        logger.error(
            "Unhandled exception on %s %s: %s",
            request.method,
            request.url.path,
            str(exc),
            exc_info=True,
        )

        # In production / non-debug mode, conceal internal details
        if settings.DEBUG:
            message = str(exc) or "Internal server error"
            details = {"type": type(exc).__name__}
        else:
            message = "An unexpected internal server error occurred."
            details = None

        error_payload = ErrorResponse(
            error=True,
            code="INTERNAL_SERVER_ERROR",
            message=message,
            details=details,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_payload.model_dump(mode="json"),
        )

