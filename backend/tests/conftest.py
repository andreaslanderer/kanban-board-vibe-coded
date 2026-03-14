import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def test_client(tmp_path_factory):
    # Use an isolated SQLite file for tests
    db_path = tmp_path_factory.mktemp("data") / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    # Ensure a minimal static export exists to satisfy the app mount
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/out"))
    os.makedirs(out_dir, exist_ok=True)
    index_path = Path(out_dir) / "index.html"
    index_path.write_text("<html><body><h1>Static Export</h1></body></html>")

    # Import app after setting env var
    from app.main import app

    with TestClient(app) as client:
        yield client
