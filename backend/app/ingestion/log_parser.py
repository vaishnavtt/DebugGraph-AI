"""
Modular log parser for DebugGraph AI.
Supports Standard Text, Python multiline exception tracebacks, JSON, and JSONL formats.
Preserves unparsed records without silent data loss.
"""
from datetime import datetime
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from app.ingestion.normalizer import normalize_severity, normalize_timestamp
from app.schemas.logs import LogEntry

# Regex detecting start of Python traceback
STACK_TRACE_START_RE = re.compile(r"^Traceback \(most recent call last\):", re.MULTILINE)
# Regex for exception summary line (e.g. ValueError: Invalid ID or requests.exceptions.Timeout: ...)
EXCEPTION_LINE_RE = re.compile(
    r"^(?P<exc_type>(?:[a-zA-Z_][a-zA-Z0-9_.]*\.)?[a-zA-Z_][a-zA-Z0-9_]*(?:Exception|Error|Fault|Timeout|Failure|Interrupt|Warning))(?::\s*(?P<exc_msg>.*))?$"
)

# Regex patterns for standard log line headers
TEXT_LOG_PATTERNS = [
    # Pattern 1: ISO/Standard Date + Level + [Service] + Message
    # Example: 2026-11-01 10:15:01 INFO [payment-service] Payment service started
    re.compile(
        r"^(?P<timestamp>\d{4}[-/]\d{2}[-/]\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?)"
        r"\s+\[?(?P<level>[A-Za-z]{3,9})\]?"
        r"(?:\s+\[(?P<service>[^\]]+)\])?"
        r"(?::|\s+-|\s+--)?\s+(?P<message>.*)$"
    ),
    # Pattern 2: ISO/Standard Date + [Service] + Level + Message
    # Example: 2026-11-01 10:15:01 [payment-service] INFO Payment service started
    re.compile(
        r"^(?P<timestamp>\d{4}[-/]\d{2}[-/]\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?)"
        r"\s+\[(?P<service>[^\]]+)\]"
        r"\s+\[?(?P<level>[A-Za-z]{3,9})\]?"
        r"(?::|\s+-|\s+--)?\s+(?P<message>.*)$"
    ),
    # Pattern 3: Pipe-separated format
    # Example: 2026-11-01 10:15:01 | INFO | payment-service | Payment service started
    re.compile(
        r"^(?P<timestamp>\d{4}[-/]\d{2}[-/]\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?)"
        r"\s*\|\s*(?P<level>[A-Za-z]{3,9})"
        r"(?:\s*\|\s*(?P<service>[^|]+))?"
        r"\s*\|\s*(?P<message>.*)$"
    ),
    # Pattern 4: Date + Message without explicit level (fallback)
    re.compile(
        r"^(?P<timestamp>\d{4}[-/]\d{2}[-/]\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?)"
        r"\s+(?P<message>.*)$"
    ),
]


def extract_exception_details(stack_trace_text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract exception class and message from the final lines of a stack trace."""
    lines = [line.strip() for line in stack_trace_text.strip().splitlines() if line.strip()]
    if not lines:
        return None, None

    # Search from bottom up for the exception line
    for line in reversed(lines):
        match = EXCEPTION_LINE_RE.match(line)
        if match:
            exc_type = match.group("exc_type")
            exc_msg = match.group("exc_msg") or ""
            return exc_type, exc_msg.strip()

    # Fallback to last line if not matching pattern
    last_line = lines[-1]
    if ":" in last_line:
        parts = last_line.split(":", 1)
        return parts[0].strip(), parts[1].strip()
    return None, last_line


class LogParser:
    """Parser supporting Text, Python Exception Stack Traces, JSON, and JSONL formats."""

    @staticmethod
    def parse_text_logs(raw_content: str, default_service: Optional[str] = None) -> Tuple[List[LogEntry], List[str]]:
        """
        Parse raw plain-text log lines, assembling multiline stack traces
        and preserving unrecognized lines as unparsed entries.
        """
        lines = raw_content.splitlines()
        entries: List[LogEntry] = []
        warnings: List[str] = []

        if not lines:
            return entries, warnings

        i = 0
        total_lines = len(lines)
        entry_counter = 1

        while i < total_lines:
            line = lines[i]
            line_no = i + 1

            # Skip blank empty lines between entries
            if not line.strip():
                i += 1
                continue

            matched = False
            for pattern in TEXT_LOG_PATTERNS:
                m = pattern.match(line)
                if m:
                    matched = True
                    groups = m.groupdict()
                    raw_ts = groups.get("timestamp")
                    raw_lvl = groups.get("level")
                    service = groups.get("service") or default_service
                    message = groups.get("message", "").strip()

                    norm_dt, norm_raw_ts = normalize_timestamp(raw_ts)
                    norm_lvl = normalize_severity(raw_lvl)

                    # Look ahead for multiline exception or continuation
                    start_line = line_no
                    end_line = line_no
                    raw_block = [line]
                    stack_trace_lines: List[str] = []
                    in_traceback = False

                    peek = i + 1
                    while peek < total_lines:
                        next_line = lines[peek]

                        # Check if next line is a new log entry header
                        is_new_entry = any(p.match(next_line) for p in TEXT_LOG_PATTERNS)
                        if is_new_entry:
                            break

                        # Check for traceback start
                        if STACK_TRACE_START_RE.match(next_line):
                            in_traceback = True

                        if in_traceback:
                            stack_trace_lines.append(next_line)
                            raw_block.append(next_line)
                            end_line = peek + 1
                            peek += 1
                        elif next_line.startswith((" ", "\t")) or not next_line.strip():
                            # Continuation line (e.g., wrapped log message)
                            raw_block.append(next_line)
                            if next_line.strip():
                                message += "\n" + next_line.strip()
                            end_line = peek + 1
                            peek += 1
                        else:
                            # Unrecognized standalone line: stop current block
                            break

                    stack_trace_str = "\n".join(stack_trace_lines) if stack_trace_lines else None
                    exc_type, exc_msg = (
                        extract_exception_details(stack_trace_str)
                        if stack_trace_str
                        else (None, None)
                    )

                    entry = LogEntry(
                        entry_id=f"log_{entry_counter}",
                        timestamp_raw=norm_raw_ts or raw_ts,
                        timestamp=norm_dt,
                        severity=norm_lvl,
                        service=service,
                        message=message,
                        exception_type=exc_type,
                        exception_message=exc_msg,
                        stack_trace=stack_trace_str,
                        start_line=start_line,
                        end_line=end_line,
                        raw_content="\n".join(raw_block),
                        parsed=True,
                        attributes={},
                    )
                    entries.append(entry)
                    entry_counter += 1
                    i = peek
                    break

            if not matched:
                # Line did not match known log header: check if it's an isolated traceback
                if STACK_TRACE_START_RE.match(line):
                    start_line = line_no
                    raw_block = [line]
                    stack_lines = [line]
                    peek = i + 1
                    while peek < total_lines:
                        next_line = lines[peek]
                        if any(p.match(next_line) for p in TEXT_LOG_PATTERNS):
                            break
                        raw_block.append(next_line)
                        stack_lines.append(next_line)
                        peek += 1

                    st_str = "\n".join(stack_lines)
                    exc_type, exc_msg = extract_exception_details(st_str)
                    entry = LogEntry(
                        entry_id=f"log_{entry_counter}",
                        timestamp_raw=None,
                        timestamp=None,
                        severity="ERROR",
                        service=default_service,
                        message=f"Unhandled exception: {exc_type or 'Exception'}: {exc_msg or ''}".strip(),
                        exception_type=exc_type,
                        exception_message=exc_msg,
                        stack_trace=st_str,
                        start_line=start_line,
                        end_line=peek,
                        raw_content="\n".join(raw_block),
                        parsed=True,
                        attributes={},
                    )
                    entries.append(entry)
                    entry_counter += 1
                    i = peek
                else:
                    # Preserve unrecognized log line as unparsed entry without data loss
                    entry = LogEntry(
                        entry_id=f"log_{entry_counter}",
                        timestamp_raw=None,
                        timestamp=None,
                        severity="UNKNOWN",
                        service=default_service,
                        message=line.strip(),
                        exception_type=None,
                        exception_message=None,
                        stack_trace=None,
                        start_line=line_no,
                        end_line=line_no,
                        raw_content=line,
                        parsed=False,
                        attributes={},
                    )
                    entries.append(entry)
                    entry_counter += 1
                    warnings.append(f"Line {line_no} does not match recognized log format; preserved as unparsed.")
                    i += 1

        return entries, warnings

    @staticmethod
    def parse_json_object(
        obj: Dict[str, Any],
        line_no: int,
        entry_idx: int,
        raw_text: str,
        default_service: Optional[str] = None,
    ) -> LogEntry:
        """Extract structured log entry fields from a Python dictionary."""
        # 1. Timestamp extraction
        ts_candidates = ["timestamp", "time", "ts", "@timestamp", "datetime", "date", "created_at"]
        raw_ts: Optional[str] = None
        for k in ts_candidates:
            if k in obj and obj[k] is not None:
                raw_ts = str(obj[k])
                break

        norm_dt, norm_raw_ts = normalize_timestamp(raw_ts)

        # 2. Severity extraction
        lvl_candidates = ["level", "severity", "log_level", "status", "loglevel"]
        raw_lvl: Optional[str] = None
        for k in lvl_candidates:
            if k in obj and obj[k] is not None:
                raw_lvl = str(obj[k])
                break

        norm_lvl = normalize_severity(raw_lvl)

        # 3. Service name extraction (never invent missing service)
        svc_candidates = ["service", "service_name", "app", "application", "component", "module"]
        service: Optional[str] = None
        for k in svc_candidates:
            if k in obj and obj[k]:
                service = str(obj[k])
                break
        if not service:
            service = default_service

        # 4. Message extraction
        msg_candidates = ["message", "msg", "log", "text", "description", "event"]
        message = ""
        for k in msg_candidates:
            if k in obj and obj[k] is not None:
                message = str(obj[k])
                break
        if not message:
            message = str(obj)

        # 5. Exception & stack trace extraction
        stack_trace: Optional[str] = None
        exc_type: Optional[str] = None
        exc_msg: Optional[str] = None

        exc_candidates = ["exception", "stack_trace", "traceback", "stacktrace", "error"]
        for k in exc_candidates:
            if k in obj and obj[k]:
                val = obj[k]
                if isinstance(val, dict):
                    exc_type = val.get("type") or val.get("class")
                    exc_msg = val.get("message")
                    stack_trace = val.get("stack_trace") or val.get("traceback") or str(val)
                elif isinstance(val, str):
                    stack_trace = val
                    extracted_type, extracted_msg = extract_exception_details(val)
                    exc_type = extracted_type
                    exc_msg = extracted_msg
                break

        # 6. Additional attributes
        reserved_keys = set(ts_candidates + lvl_candidates + svc_candidates + msg_candidates + exc_candidates)
        attributes = {k: v for k, v in obj.items() if k not in reserved_keys}

        return LogEntry(
            entry_id=f"log_{entry_idx}",
            timestamp_raw=norm_raw_ts or raw_ts,
            timestamp=norm_dt,
            severity=norm_lvl,
            service=service,
            message=message,
            exception_type=exc_type,
            exception_message=exc_msg,
            stack_trace=stack_trace,
            start_line=line_no,
            end_line=line_no,
            raw_content=raw_text,
            parsed=True,
            attributes=attributes,
        )

    @classmethod
    def parse_json_content(
        cls, raw_content: str, default_service: Optional[str] = None
    ) -> Tuple[List[LogEntry], List[str]]:
        """Parse structured JSON log file (array of objects or single object)."""
        entries: List[LogEntry] = []
        warnings: List[str] = []

        try:
            data = json.loads(raw_content)
        except json.JSONDecodeError as exc:
            warnings.append(f"JSON decode failed: {exc.msg} at line {exc.lineno}")
            return entries, warnings

        if isinstance(data, list):
            for idx, item in enumerate(data, start=1):
                if isinstance(item, dict):
                    entry = cls.parse_json_object(
                        obj=item,
                        line_no=idx,
                        entry_idx=idx,
                        raw_text=json.dumps(item),
                        default_service=default_service,
                    )
                    entries.append(entry)
                else:
                    entries.append(
                        LogEntry(
                            entry_id=f"log_{idx}",
                            message=str(item),
                            start_line=idx,
                            end_line=idx,
                            raw_content=json.dumps(item),
                            parsed=False,
                            severity="UNKNOWN",
                            service=default_service,
                        )
                    )
                    warnings.append(f"Item {idx} is not a JSON object.")
        elif isinstance(data, dict):
            entry = cls.parse_json_object(
                obj=data,
                line_no=1,
                entry_idx=1,
                raw_text=json.dumps(data),
                default_service=default_service,
            )
            entries.append(entry)
        else:
            warnings.append("JSON root element is neither a list nor an object.")

        return entries, warnings

    @classmethod
    def parse_jsonl_content(
        cls, raw_content: str, default_service: Optional[str] = None
    ) -> Tuple[List[LogEntry], List[str]]:
        """Parse JSON Lines (JSONL) formatted log content."""
        entries: List[LogEntry] = []
        warnings: List[str] = []
        lines = raw_content.splitlines()

        entry_idx = 1
        for line_no, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue

            try:
                obj = json.loads(stripped)
                if isinstance(obj, dict):
                    entry = cls.parse_json_object(
                        obj=obj,
                        line_no=line_no,
                        entry_idx=entry_idx,
                        raw_text=line,
                        default_service=default_service,
                    )
                    entries.append(entry)
                    entry_idx += 1
                else:
                    entries.append(
                        LogEntry(
                            entry_id=f"log_{entry_idx}",
                            message=str(obj),
                            start_line=line_no,
                            end_line=line_no,
                            raw_content=line,
                            parsed=False,
                            severity="UNKNOWN",
                            service=default_service,
                        )
                    )
                    entry_idx += 1
                    warnings.append(f"Line {line_no} JSON value is not an object.")
            except json.JSONDecodeError as exc:
                # Preserve malformed line as unparsed entry without discarding
                entries.append(
                    LogEntry(
                        entry_id=f"log_{entry_idx}",
                        message=stripped,
                        start_line=line_no,
                        end_line=line_no,
                        raw_content=line,
                        parsed=False,
                        severity="UNKNOWN",
                        service=default_service,
                    )
                )
                entry_idx += 1
                warnings.append(f"Line {line_no} is invalid JSON: {exc.msg}")

        return entries, warnings

