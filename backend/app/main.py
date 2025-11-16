"""Data Detective Academy - Main Application"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_db_and_tables
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

# Configure CORS to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],  # Vite dev server ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(progress.router)
app.include_router(leaderboard.router)
app.include_router(hints.router)
app.include_router(reports.router)
app.include_router(analytics.router)
app.include_router(export.router)
app.include_router(bulk_import.router)
app.include_router(challenges.router)
app.include_router(datasets.router)
app.include_router(custom_challenges.router)


@app.get("/")
def read_root():
    """
    Root endpoint - welcome message
    Returns:
        dict: welcome message and api version
    """
    return {"message": "Welcome to Data Detective Academy API", "version": "1.0.0"}


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
    return {"app": "Data Detective Academy", "environment": "development"}
