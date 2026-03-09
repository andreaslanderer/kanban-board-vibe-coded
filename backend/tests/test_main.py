import os
from fastapi.testclient import TestClient

# ensure a dummy static export exists before app is imported
# path should mirror the one computed in app.main (two levels up to repo root)
out_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../frontend/out")
)
os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(out_dir, "index.html"), "w") as f:
    f.write("<html><body><h1>Static Export</h1></body></html>")

from app.main import app

client = TestClient(app)

def test_read_root_serves_static():
    response = client.get("/")
    assert response.status_code == 200
    assert "Static Export" in response.text


def test_api_hello():
    response = client.get("/api/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "Backend is working"}
