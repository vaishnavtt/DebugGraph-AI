"""
Integration tests for the /api/v1/logs/upload endpoint.
Validates file upload, validation, rejection of invalid extensions,
size limit enforcement, path traversal protection, and response schemas.
"""
import io
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.schemas.logs import LogUploadResponse

client = TestClient(app)


def test_upload_standard_text_log_success() -> None:
    """Validate successful multipart upload of a standard .log file."""
    log_content = (
        b"2026-11-01 10:15:01 INFO [payment-service] Initializing service\n"
        b"2026-11-01 10:15:05 WARNING [payment-service] High latency detected: 780ms\n"
        b"2026-11-01 10:15:10 ERROR [payment-service] Gateway timeout\n"
        b"Traceback (most recent call last):\n"
        b"  File \"/app/pay.py\", line 10, in charge\n"
        b"    raise TimeoutError(\"timed out\")\n"
        b"TimeoutError: timed out\n"
    )

    response = client.post(
        f"{settings.API_V1_PREFIX}/logs/upload",
        files={"file": ("payment.log", io.BytesIO(log_content), "text/plain")},
    )

    assert response.status_code == 201
    data = response.json()

    # Validate against Pydantic schema
    validated = LogUploadResponse(**data)
    assert validated.original_filename == "payment.log"
    assert validated.format_detected == "standard_text"
    assert validated.total_entries == 3
    assert validated.parsed_entries == 3
    assert validated.error_count == 1
    assert validated.warning_count == 1
    assert validated.ingestion_id.startswith("ingest_")


def test_upload_json_log_success() -> None:
    """Validate successful upload and parsing of a structured .json file."""
    json_content = (
        b'[\n'
        b'  {"timestamp": "2026-11-01T10:15:01Z", "level": "INFO", "service": "auth-service", "message": "Booted"},\n'
        b'  {"timestamp": "2026-11-01T10:15:05Z", "level": "ERROR", "service": "auth-service", "message": "Auth failure"}\n'
        b']'
    )

    response = client.post(
        f"{settings.API_V1_PREFIX}/logs/upload",
        files={"file": ("auth_logs.json", io.BytesIO(json_content), "application/json")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["format_detected"] == "json"
    assert data["total_entries"] == 2
    assert data["error_count"] == 1


def test_upload_jsonl_log_success() -> None:
    """Validate successful upload and parsing of a .jsonl file."""
    jsonl_content = (
        b'{"timestamp": "2026-11-01T10:15:01Z", "level": "INFO", "service": "cart", "message": "Cart created"}\n'
        b'{"timestamp": "2026-11-01T10:15:02Z", "level": "CRITICAL", "service": "cart", "message": "Memory low"}\n'
    )

    response = client.post(
        f"{settings.API_V1_PREFIX}/logs/upload",
        files={"file": ("cart.jsonl", io.BytesIO(jsonl_content), "application/x-ndjson")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["format_detected"] == "jsonl"
    assert data["total_entries"] == 2
    assert data["critical_count"] == 1


def test_upload_empty_file_rejected() -> None:
    """Validate rejection of 0-byte file uploads."""
    response = client.post(
        f"{settings.API_V1_PREFIX}/logs/upload",
        files={"file": ("empty.log", io.BytesIO(b""), "text/plain")},
    )

    assert response.status_code == 400
    data = response.json()
    assert data["error"] is True
    assert data["code"] == "EMPTY_FILE"


def test_upload_whitespace_only_file_rejected() -> None:
    """Validate rejection of whitespace-only files."""
    response = client.post(
        f"{settings.API_V1_PREFIX}/logs/upload",
        files={"file": ("blank.log", io.BytesIO(b"   \n\t  \n  "), "text/plain")},
    )

    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "EMPTY_FILE"


def test_upload_unsupported_extension_rejected() -> None:
    """Validate rejection of disallowed file extensions (e.g., .exe, .py, .pdf)."""
    response = client.post(
        f"{settings.API_V1_PREFIX}/logs/upload",
        files={"file": ("malicious.exe", io.BytesIO(b"binary data"), "application/octet-stream")},
    )

    assert response.status_code == 400
    data = response.json()
    assert data["error"] is True
    assert data["code"] == "UNSUPPORTED_FILE_TYPE"
    assert "unsupported" in data["message"].lower()


def test_upload_oversized_file_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validate enforcement of maximum upload size limit."""
    monkeypatch.setattr(settings, "MAX_LOG_UPLOAD_SIZE_BYTES", 50)

    large_content = b"A" * 100
    response = client.post(
        f"{settings.API_V1_PREFIX}/logs/upload",
        files={"file": ("large.log", io.BytesIO(large_content), "text/plain")},
    )

    assert response.status_code == 413
    data = response.json()
    assert data["error"] is True
    assert data["code"] == "FILE_TOO_LARGE"


def test_upload_malformed_json_handling() -> None:
    """Validate clear error response on malformed JSON payload."""
    malformed_json = b"{\n  \"timestamp\": \"2026-11-01\",\n  \"unclosed\": \n"

    response = client.post(
        f"{settings.API_V1_PREFIX}/logs/upload",
        files={"file": ("broken.json", io.BytesIO(malformed_json), "application/json")},
    )

    assert response.status_code == 400
    data = response.json()
    assert data["error"] is True
    assert data["code"] == "MALFORMED_JSON"


def test_upload_path_traversal_sanitized() -> None:
    """Ensure path traversal characters in filenames are sanitized."""
    log_content = b"2026-11-01 10:15:01 INFO [svc] Safe message\n"
    response = client.post(
        f"{settings.API_V1_PREFIX}/logs/upload",
        files={"file": ("../../../../etc/passwd.log", io.BytesIO(log_content), "text/plain")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["original_filename"] == "passwd.log"
    assert "/" not in data["original_filename"]
    assert ".." not in data["original_filename"]

