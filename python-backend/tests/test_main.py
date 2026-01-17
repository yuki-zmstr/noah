"""Test main application functionality."""


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app_name" in data
    assert "version" in data


def test_api_docs_available(client):
    """Test that API documentation is available."""
    response = client.get("/docs")
    assert response.status_code == 200
