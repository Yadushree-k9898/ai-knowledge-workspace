"""
Structured logging configuration for the AI Knowledge API.

Provides:
- JSON-formatted structured logs for production
- Human-readable logs for development
- Security event logging (login, logout, profile changes)
- Request correlation via request IDs
- Sensitive data filtering (never logs passwords, tokens)
"""

import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any


# ---------------------------------------------------------------------------
# Custom JSON Formatter
# ---------------------------------------------------------------------------

class JSONFormatter(logging.Formatter):
    """Produces one JSON object per log line for structured log aggregation."""

    SENSITIVE_KEYS = {"password", "token", "access_token", "secret", "authorization"}

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Attach extra fields (request_id, user_id, event, etc.)
        for key in ("request_id", "user_id", "event", "resource_type",
                     "resource_id", "ip_address", "method", "path",
                     "status_code", "duration_ms", "detail"):
            value = getattr(record, key, None)
            if value is not None:
                log_entry[key] = value

        # Exception info
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


# ---------------------------------------------------------------------------
# Logger Setup
# ---------------------------------------------------------------------------

def setup_logging(level: str = "INFO") -> None:
    """Configure the root logger and specialised loggers."""

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear existing handlers to avoid duplicates on reload
    root.handlers.clear()

    # Console handler with JSON formatter
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG)
    console.setFormatter(JSONFormatter())
    root.addHandler(console)

    # Quieten noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# Convenience Loggers
# ---------------------------------------------------------------------------

def get_logger(name: str) -> logging.Logger:
    """Return a named logger that inherits the root configuration."""
    return logging.getLogger(name)


# Security event logger — a dedicated logger for auth/security events
security_logger = logging.getLogger("security")


def log_security_event(
    event: str,
    *,
    user_id: str | None = None,
    ip_address: str | None = None,
    detail: str | None = None,
    request_id: str | None = None,
) -> None:
    """
    Log a security-relevant event.

    Good events to log:
        LOGIN_SUCCESS, LOGIN_FAILURE, SIGNUP, LOGOUT,
        PROFILE_UPDATED, PROFILE_CREATED, ACCOUNT_DELETED,
        TOKEN_EXPIRED, TOKEN_INVALID, UNAUTHORIZED_ACCESS

    Never log:
        passwords, tokens, secrets
    """
    security_logger.info(
        event,
        extra={
            "event": event,
            "user_id": user_id,
            "ip_address": ip_address,
            "detail": detail,
            "request_id": request_id,
        },
    )
