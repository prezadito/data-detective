"""Data Detective Academy - Main Application"""

from fastapi import FastAPI

app = FastAPI(
    title="Data Detective Academy API",
    description="Backend API for Data Detective Academy Learning Platform",
    version="1.0.0",
)


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
