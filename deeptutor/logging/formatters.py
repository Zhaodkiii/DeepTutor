"""Formatters for DeepTutor's stdlib logging pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
import re
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .context import LOG_CONTEXT_FIELDS, current_log_context

_TOKEN_QUERY_PATTERN = re.compile(r"(token=)([^&\s]+)", re.IGNORECASE)
_BEARER_PATTERN = re.compile(r"(Bearer\s+)([A-Za-z0-9\-_\.=]+)", re.IGNORECASE)
_JWT_PATTERN = re.compile(r"\beyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\b")


def redact_sensitive(text: str) -> str:
    """Remove JWTs and query tokens from log text."""
    if not text:
        return text

    redacted = _TOKEN_QUERY_PATTERN.sub(r"\1<redacted>", text)
    redacted = _BEARER_PATTERN.sub(r"\1<redacted>", redacted)
    redacted = _JWT_PATTERN.sub("<redacted>", redacted)

    if "?" in redacted:
        parts = urlsplit(redacted)
        if parts.query:
            query = urlencode([
                (key, "<redacted>" if key.lower() == "token" else value)
                for key, value in parse_qsl(parts.query, keep_blank_values=True)
            ])
            redacted = urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))

    return redacted


class ContextFilter(logging.Filter):
    """Attach contextvars and explicit record fields to each LogRecord."""

    def filter(self, record: logging.LogRecord) -> bool:
        context = current_log_context()
        for key in LOG_CONTEXT_FIELDS:
            value = getattr(record, key, None)
            if value is not None:
                context[key] = value
        record.log_context = context
        return True


class JsonlFormatter(logging.Formatter):
    """One structured JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_sensitive(record.getMessage()),
            "context": getattr(record, "log_context", {}) or {},
        }
        if record.exc_info:
            entry["exception"] = redact_sensitive(self.formatException(record.exc_info))
        return json.dumps(entry, ensure_ascii=False, default=str)


class ConsoleFormatter(logging.Formatter):
    """Small human-readable formatter for local development."""

    def format(self, record: logging.LogRecord) -> str:
        context = getattr(record, "log_context", {}) or {}
        stage = f" @{context['stage']}" if context.get("stage") else ""
        task = f" #{context['task_id']}" if context.get("task_id") else ""
        return f"{record.levelname:<7} {record.name}{stage}{task} - {redact_sensitive(record.getMessage())}"
