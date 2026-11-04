"""
Log normalization utilities for DebugGraph AI.
Standardizes severity levels and parses timestamps into timezone-aware UTC.
"""
from datetime import datetime, timezone
import re
from typing import Optional, Tuple

# Canonical severity set
VALID_SEVERITIES = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "UNKNOWN"}

# Severity normalization mapping
SEVERITY_MAP = {
    # Debug
    "DEBUG": "DEBUG",
    "DBG": "DEBUG",
    "TRACE": "DEBUG",
    "FINE": "DEBUG",
    "FINER": "DEBUG",
    "FINEST": "DEBUG",
    "D": "DEBUG",
    # Info
    "INFO": "INFO",
    "INF": "INFO",
    "INFORMATION": "INFO",
    "NOTICE": "INFO",
    "I": "INFO",
    # Warning
    "WARN": "WARNING",
    "WARNING": "WARNING",
    "WRN": "WARNING",
    "W": "WARNING",
    # Error
    "ERROR": "ERROR",
    "ERR": "ERROR",
    "ERRO": "ERROR",
    "FAIL": "ERROR",
    "FAILURE": "ERROR",
    "E": "ERROR",
    # Critical
    "CRIT": "CRITICAL",
    "CRITICAL": "CRITICAL",
    "FATAL": "CRITICAL",
    "EMERG": "CRITICAL",
    "EMERGENCY": "CRITICAL",
    "SEVERE": "CRITICAL",
    "PANIC": "CRITICAL",
}


def normalize_severity(raw_level: Optional[str]) -> str:
    """
    Normalize arbitrary severity strings to one of:
    DEBUG, INFO, WARNING, ERROR, CRITICAL, UNKNOWN.
    """
    if not raw_level:
        return "UNKNOWN"

    cleaned = raw_level.strip().upper()
    return SEVERITY_MAP.get(cleaned, "UNKNOWN")


# Common datetime format patterns
DATETIME_FORMATS = [
    # ISO 8601 formats
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%d %H:%M:%S%z",
    "%Y-%m-%d %H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S.%fZ",
    # Naive ISO formats
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
    # Standard logs (space-separated)
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S,%f",  # Python standard logging default
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S.%f",
    "%d/%b/%Y:%H:%M:%S %z",  # Nginx / Apache Common Log
]


def normalize_timestamp(raw_timestamp: Optional[str]) -> Tuple[Optional[datetime], Optional[str]]:
    """
    Normalize raw timestamp string into a timezone-aware UTC datetime.
    
    Returns:
        (normalized_utc_datetime_or_None, original_raw_string_or_None)
    """
    if not raw_timestamp:
        return None, None

    raw_str = str(raw_timestamp).strip()
    if not raw_str:
        return None, None

    # Handle numeric UNIX epoch timestamps (seconds or milliseconds)
    if re.fullmatch(r"^\d{10}(\.\d+)?$", raw_str):
        try:
            dt = datetime.fromtimestamp(float(raw_str), tz=timezone.utc)
            return dt, raw_str
        except (ValueError, OverflowError):
            pass

    if re.fullmatch(r"^\d{13}$", raw_str):  # Milliseconds epoch
        try:
            dt = datetime.fromtimestamp(float(raw_str) / 1000.0, tz=timezone.utc)
            return dt, raw_str
        except (ValueError, OverflowError):
            pass

    # Try datetime formats
    clean_ts = raw_str
    if clean_ts.endswith("Z"):
        clean_ts = clean_ts[:-1] + "+0000"

    for fmt in DATETIME_FORMATS:
        try:
            dt = datetime.strptime(clean_ts, fmt)
            # If naive, assume UTC as standard operational baseline
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt, raw_str
        except ValueError:
            continue

    # Try fromisoformat as fallback
    try:
        dt = datetime.fromisoformat(raw_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt, raw_str
    except (ValueError, TypeError):
        pass

    # Return None for datetime if unparseable, preserving original raw string
    return None, raw_str

