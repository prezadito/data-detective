"""
Logging configuration for Data Detective Academy.

Provides structured logging with appropriate formatters for development
and production environments.
"""

import logging
import sys
import os
from typing import Optional


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging in production.

    Outputs logs as JSON for easy parsing by log aggregation tools.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string."""
        import json
        from datetime import datetime

        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        return json.dumps(log_data)


class ReadableFormatter(logging.Formatter):
    """
    Human-readable formatter for development.

    Outputs colorized logs with clear structure for console viewing.
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
        "RESET": "\033[0m",       # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors and readable structure."""
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            colored_level = f"{self.COLORS[levelname]}{levelname:8s}{self.COLORS['RESET']}"
        else:
            colored_level = f"{levelname:8s}"

        # Format timestamp
        timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S")

        # Build log message
        log_parts = [
            f"{timestamp}",
            f"{colored_level}",
            f"[{record.name}]",
            f"{record.getMessage()}",
        ]

        # Add extra context if present
        extras = []
        if hasattr(record, "request_id"):
            extras.append(f"request_id={record.request_id}")
        if hasattr(record, "user_id"):
            extras.append(f"user_id={record.user_id}")
        if hasattr(record, "duration_ms"):
            extras.append(f"duration={record.duration_ms}ms")

        if extras:
            log_parts.append(f"({', '.join(extras)})")

        message = " ".join(log_parts)

        # Add exception info if present
        if record.exc_info:
            message += "\n" + self.formatException(record.exc_info)

        return message


def setup_logging(
    level: Optional[str] = None,
    log_format: Optional[str] = None,
) -> logging.Logger:
    """
    Configure application logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               Defaults to LOG_LEVEL env var or INFO.
        log_format: Format style ('json' or 'text').
                   Defaults to LOG_FORMAT env var or 'text' in development.

    Returns:
        Configured root logger instance.

    Example:
        >>> logger = setup_logging(level="INFO", log_format="json")
        >>> logger.info("Application started")
    """
    # Get configuration from environment or use defaults
    log_level = level or os.getenv("LOG_LEVEL", "INFO")
    log_format_type = log_format or os.getenv("LOG_FORMAT", "text")
    environment = os.getenv("ENVIRONMENT", "development")

    # Auto-select format based on environment if not explicitly set
    if log_format is None and log_format_type == "text":
        if environment == "production":
            log_format_type = "json"

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    # Set formatter based on format type
    if log_format_type == "json":
        formatter = JSONFormatter()
    else:
        formatter = ReadableFormatter()

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Configure third-party loggers to reduce noise
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing request")
    """
    return logging.getLogger(name)
