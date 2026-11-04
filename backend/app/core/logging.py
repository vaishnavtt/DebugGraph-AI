"""
Structured application logging configuration for DebugGraph AI.
Provides unified log formatting with timestamps, severity levels, and module contexts.
"""
import logging
import sys
from typing import Optional


class StructuredFormatter(logging.Formatter):
    """Custom formatter producing consistent, structured log records."""

    FORMAT = (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
    )
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self) -> None:
        super().__init__(fmt=self.FORMAT, datefmt=self.DATE_FORMAT)


def setup_logging(log_level: Optional[str] = None) -> None:
    """
    Configure application-wide structured logging.
    
    Args:
        log_level: Desired log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   Defaults to INFO or the configured setting.
    """
    level_name = (log_level or "INFO").upper()
    numeric_level = getattr(logging, level_name, logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)

    # Configure uvicorn loggers to use structured format
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        uv_logger = logging.getLogger(logger_name)
        uv_logger.handlers = []
        uv_logger.propagate = True


def get_logger(name: str) -> logging.Logger:
    """
    Obtain a named logger instance for a given module.

    Args:
        name: Typically __name__ of the calling module.

    Returns:
        Configured logging.Logger.
    """
    return logging.getLogger(name)

