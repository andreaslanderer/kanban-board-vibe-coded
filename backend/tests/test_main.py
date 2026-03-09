from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_read_root_returns_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "Hello from backend" in response.text


def test_api_hello():
    response = client.get("/api/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "Backend is working"}
