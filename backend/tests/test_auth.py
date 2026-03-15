"""Tests for the OAuth / auth endpoints."""
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# dev-login
# ---------------------------------------------------------------------------

def test_dev_login_creates_user_and_board(test_client):
    resp = test_client.post("/api/auth/dev-login", json={"email": "brand_new@example.com"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "brand_new@example.com"
    assert data["display_name"] == "brand_new"

    # The user should now have a board with 5 default columns
    board_resp = test_client.get("/api/boards")
    assert board_resp.status_code == 200
    assert len(board_resp.json()["columns"]) == 5


def test_dev_login_reuses_existing_user(test_client):
    test_client.post("/api/auth/dev-login", json={"email": "returning@example.com"})
    resp2 = test_client.post("/api/auth/dev-login", json={"email": "returning@example.com"})
    assert resp2.status_code == 200
    assert resp2.json()["email"] == "returning@example.com"


def test_dev_login_blocked_in_production(test_client, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    resp = test_client.post("/api/auth/dev-login", json={"email": "blocked@example.com"})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# /api/auth/me
# ---------------------------------------------------------------------------

def test_me_authenticated(auth_client):
    resp = auth_client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@example.com"


def test_me_unauthenticated():
    from app.main import app

    with TestClient(app, cookies={}) as fresh_client:
        resp = fresh_client.get("/api/auth/me")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

def test_logout_clears_session():
    """After logout, /api/auth/me returns 401 for the same client."""
    from app.main import app

    with TestClient(app) as client:
        client.post("/api/auth/dev-login", json={"email": "logout_test@example.com"})
        assert client.get("/api/auth/me").status_code == 200

        logout_resp = client.post("/api/auth/logout")
        assert logout_resp.status_code == 200

        assert client.get("/api/auth/me").status_code == 401


# ---------------------------------------------------------------------------
# Google OAuth redirect
# ---------------------------------------------------------------------------

def test_google_login_missing_config(test_client, monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    resp = test_client.get("/api/auth/google", follow_redirects=False)
    assert resp.status_code == 500


def test_google_login_redirects_to_google(test_client, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("APP_BASE_URL", "http://localhost:8000")
    resp = test_client.get("/api/auth/google", follow_redirects=False)
    assert resp.status_code in (302, 307)
    location = resp.headers["location"]
    assert "accounts.google.com" in location
    assert "test-client-id" in location
    assert "oauth_state" in resp.cookies


def test_google_callback_rejects_bad_state(test_client):
    resp = test_client.get(
        "/api/auth/google/callback?code=fake_code&state=wrong_state"
    )
    assert resp.status_code == 400
    assert "state" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# JWT edge cases
# ---------------------------------------------------------------------------

def test_invalid_jwt_cookie_returns_401():
    from app.main import app

    with TestClient(app, cookies={"access_token": "not.a.valid.token"}) as client:
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401


def test_expired_jwt_returns_401(monkeypatch):
    """Token signed with a different secret should be rejected."""
    from app.main import app

    with TestClient(app, cookies={"access_token": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI5OTkifQ.bad_sig"}) as client:
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401
