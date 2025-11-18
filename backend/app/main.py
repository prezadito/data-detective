"""Data Detective Academy - Main Application"""

from contextlib import asynccontextmanager
from pathlib import Path
import os
import time
from datetime import datetime
from dotenv import load_dotenv

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.database import create_db_and_tables

# Load environment variables FIRST
load_dotenv()

# Initialize Sentry (must be before app creation)
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

# Initialize logging
from app.logging_config import setup_logging, get_logger

# Setup logging before anything else
setup_logging()
logger = get_logger(__name__)

# Configure Sentry if DSN is provided
sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=os.getenv("SENTRY_ENVIRONMENT", os.getenv("ENVIRONMENT", "development")),
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            LoggingIntegration(
                level=None,  # Capture all levels (filtering done by logger)
                event_level=None,  # Don't automatically send log records as events
            ),
        ],
        # Filter sensitive data
        before_send=lambda event, hint: _filter_sensitive_data(event),
    )
    logger.info(f"Sentry initialized for environment: {os.getenv('ENVIRONMENT', 'development')}")
else:
    logger.warning("SENTRY_DSN not set - error tracking disabled")


def _filter_sensitive_data(event: dict) -> dict:
    """
    Filter sensitive data from Sentry events.

    Removes passwords, tokens, and other sensitive fields.
    """
    # Filter request data
    if "request" in event:
        request_data = event["request"]

        # Filter headers
        if "headers" in request_data:
            sensitive_headers = ["authorization", "cookie", "x-api-key"]
            for header in sensitive_headers:
                if header in request_data["headers"]:
                    request_data["headers"][header] = "[Filtered]"

        # Filter request body
        if "data" in request_data:
            sensitive_fields = ["password", "token", "secret", "api_key"]
            if isinstance(request_data["data"], dict):
                for field in sensitive_fields:
                    if field in request_data["data"]:
                        request_data["data"][field] = "[Filtered]"

    return event
from app.routes import (
    auth,
    users,
    progress,
    leaderboard,
    hints,
    reports,
    analytics,
    export,
    bulk_import,
    challenges,
    datasets,
    custom_challenges,
    marketing,
)


# Track application start time for uptime calculation
APP_START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup: Creates database tables if they don't exist
    logger.info("Application starting up...")
    create_db_and_tables()
    logger.info("Database tables created/verified")
    logger.info("Application startup complete")
    yield
    # Shutdown: cleanup code would go here if needed
    logger.info("Application shutting down...")


app = FastAPI(
    title="Data Detective Academy API",
    description="Backend API for Data Detective Academy Learning Platform",
    version="1.0.0",
    lifespan=lifespan,
)


# Global exception handler for unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for all unhandled exceptions.

    Logs the exception with full context and returns a clean error response.
    Sends exception to Sentry if configured.
    """
    # Get request ID if available
    request_id = getattr(request.state, "request_id", "unknown")

    # Log the exception
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
        },
        exc_info=True,
    )

    # Capture in Sentry if configured
    if sentry_dsn:
        sentry_sdk.capture_exception(exc)

    # Return clean error response (don't leak stack traces)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. We've been notified and will investigate.",
            "request_id": request_id,
        },
        headers={"X-Request-ID": request_id},
    )


# Security and Performance Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security and performance headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Cache control for different content types
        if request.url.path.startswith("/static/"):
            # Cache static files for 1 year
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif request.url.path in [
            "/",
            "/features",
            "/pricing",
            "/about",
            "/contact",
            "/privacy",
            "/terms",
        ]:
            # Cache marketing pages for 1 hour, allow revalidation
            response.headers[
                "Cache-Control"
            ] = "public, max-age=3600, must-revalidate"
        elif request.url.path in ["/robots.txt", "/sitemap.xml"]:
            # Cache robots.txt and sitemap for 1 day
            response.headers["Cache-Control"] = "public, max-age=86400"
        else:
            # API endpoints: no caching
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"

        return response


# Add compression middleware (compress responses > 500 bytes)
app.add_middleware(GZipMiddleware, minimum_size=500)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Configure CORS to allow frontend requests
# Load allowed origins from environment variable (comma-separated list)
# Default to localhost ports for development
allowed_origins_env = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173"
)
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware (logs all requests with timing)
from app.middleware import RequestLoggingMiddleware
app.add_middleware(RequestLoggingMiddleware)

# Mount static files (CSS, images, etc.) for marketing pages
static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Include routers
# NOTE: Order matters! Custom challenges must come before challenges
# to avoid route conflicts (/challenges/custom vs /challenges/{unit_id})
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(progress.router)
app.include_router(leaderboard.router)
app.include_router(hints.router)
app.include_router(reports.router)
app.include_router(analytics.router)
app.include_router(export.router)
app.include_router(bulk_import.router)
app.include_router(datasets.router)
app.include_router(custom_challenges.router)  # Before challenges!
app.include_router(challenges.router)

# Include marketing router LAST (serves "/" with HTML landing page)
app.include_router(marketing.router)


@app.get("/health")
def health_check():
    """
    Enhanced health check endpoint with database connectivity check.

    Returns:
        dict: Health status with detailed checks
            - status: "healthy" (all OK), "degraded" (partial issues), "unhealthy" (critical issues)
            - timestamp: ISO-8601 timestamp
            - version: Application version
            - uptime_seconds: Seconds since application start
            - checks: Dictionary of individual health checks
    """
    from app.database import engine
    from sqlmodel import text

    # Initialize checks
    checks = {}
    overall_status = "healthy"

    # Check database connectivity
    try:
        with engine.connect() as connection:
            # Simple query to verify database is responsive
            connection.execute(text("SELECT 1"))
            checks["database"] = "ok"
    except Exception as exc:
        logger.error(f"Database health check failed: {exc}", exc_info=True)
        checks["database"] = "error"
        overall_status = "unhealthy"

    # Calculate uptime
    uptime_seconds = int(time.time() - APP_START_TIME)

    # Build response
    response = {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "uptime_seconds": uptime_seconds,
        "checks": checks,
    }

    # Return appropriate status code
    status_code = 200 if overall_status == "healthy" else 503

    return JSONResponse(content=response, status_code=status_code)


@app.get("/api/info")
def api_info():
    """
    API info endpoint
    Returns:
        dict: API name and environment
    """
    environment = os.getenv("ENVIRONMENT", "development")
    return {"app": "Data Detective Academy", "environment": environment}
