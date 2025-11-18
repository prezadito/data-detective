"""
Request logging middleware for Data Detective Academy.

Logs all HTTP requests with timing, status codes, and user context.
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.logging_config import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests with detailed context.

    Logs:
    - Request method and path
    - Response status code
    - Request duration in milliseconds
    - User ID (if authenticated)
    - Request ID (generated UUID for tracing)

    The request ID is also added to response headers as X-Request-ID.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log details.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response with added X-Request-ID header
        """
        # Generate unique request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Start timing
        start_time = time.time()

        # Extract user info if available (set by auth dependency)
        user_id = None
        if hasattr(request.state, "user"):
            user_id = getattr(request.state.user, "id", None)

        # Process request
        try:
            response = await call_next(request)
        except Exception as exc:
            # Log the exception with context
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "duration_ms": duration_ms,
                    "method": request.method,
                    "path": request.url.path,
                },
                exc_info=True,
            )
            # Re-raise to let FastAPI's exception handlers deal with it
            raise

        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        # Log based on status code
        status_code = response.status_code
        log_message = f"{request.method} {request.url.path} - {status_code}"

        extra_context = {
            "request_id": request_id,
            "user_id": user_id,
            "duration_ms": duration_ms,
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code,
        }

        # Choose log level based on status code
        if status_code >= 500:
            # Server errors - ERROR level
            logger.error(log_message, extra=extra_context)
        elif status_code >= 400:
            # Client errors - WARNING level
            logger.warning(log_message, extra=extra_context)
        else:
            # Success - INFO level
            logger.info(log_message, extra=extra_context)

        return response
