"""
Test the main FastAPI application
"""

from fastapi.testclient import TestClient


def test_root_endpoint():
    """Test the root endpoint returns a welcome message"""
    from app.main import app

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to Data Detective Academy API",
        "version": "1.0.0",
    }


def test_health_endpoint():
    """Test that health check endpoint works"""
    from app.main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_api_info_endpoint():
    """Test that API info endpoint works"""
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/info")
    assert response.status_code == 200
    assert response.json() == {
        "app": "Data Detective Academy",
        "environment": "development",
    }
