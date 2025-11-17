"""Data Detective Academy - Main Application"""

from contextlib import asynccontextmanager
from pathlib import Path
import os
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.database import create_db_and_tables

# Load environment variables
load_dotenv()
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup: Creates database tables if they don't exist
    create_db_and_tables()
    yield
    # Shutdown: cleanup code would go here if needed


app = FastAPI(
    title="Data Detective Academy API",
    description="Backend API for Data Detective Academy Learning Platform",
    version="1.0.0",
    lifespan=lifespan,
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
    Health check endpoint
    Returns:
        dict: Health status
    """
    return {"status": "healthy"}


@app.get("/api/info")
def api_info():
    """
    API info endpoint
    Returns:
        dict: API name and environment
    """
    environment = os.getenv("ENVIRONMENT", "development")
    return {"app": "Data Detective Academy", "environment": environment}
