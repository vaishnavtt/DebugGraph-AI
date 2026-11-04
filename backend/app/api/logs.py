"""
Log Ingestion API Endpoints for DebugGraph AI.
Provides multipart upload endpoints for application logs (.log, .txt, .json, .jsonl).
"""
from typing import Optional
from fastapi import APIRouter, File, Query, UploadFile, status

from app.schemas.logs import LogUploadResponse
from app.services.log_ingestion_service import LogIngestionService

router = APIRouter(prefix="/logs", tags=["Logs"])


@router.post(
    "/upload",
    response_model=LogUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and Ingest Application Log File",
    description=(
        "Upload an application log file (.log, .txt, .json, .jsonl) up to 10 MB. "
        "Extracts structured timestamps, normalized severities, exception stack traces, "
        "and event correlation groups."
    ),
)
async def upload_log_file(
    file: UploadFile = File(
        ...,
        description="Multipart log file payload (.log, .txt, .json, or .jsonl)",
    ),
    service_name: Optional[str] = Query(
        default=None,
        description="Optional default service name applied when not detectable within log lines",
    ),
) -> LogUploadResponse:
    """Handle multipart file upload, validate, parse, normalize, and correlate."""
    raw_bytes = await file.read()
    return LogIngestionService.process_log_upload(
        raw_bytes=raw_bytes,
        original_filename=file.filename,
        default_service=service_name,
    )

