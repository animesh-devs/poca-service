from fastapi.testclient import TestClient
import pytest

from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "name" in response.json()
    assert "description" in response.json()
    assert "version" in response.json()
    assert "documentation" in response.json()

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
