"""Data Detective Academy - Main Application"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import create_db_and_tables
from app.routes import auth, users, progress, leaderboard


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

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(progress.router)
app.include_router(leaderboard.router)


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
