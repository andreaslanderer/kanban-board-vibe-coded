"""Tests verifying that users cannot access or modify each other's resources."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def user_a_client(test_client):
    """Authenticated client for user_a@example.com."""
    from app.main import app

    with TestClient(app) as client:
        resp = client.post("/api/auth/dev-login", json={"email": "user_a@example.com"})
        assert resp.status_code == 200
        yield client


@pytest.fixture(scope="module")
def user_b_client(test_client):
    """Authenticated client for user_b@example.com."""
    from app.main import app

    with TestClient(app) as client:
        resp = client.post("/api/auth/dev-login", json={"email": "user_b@example.com"})
        assert resp.status_code == 200
        yield client


@pytest.fixture(scope="module")
def user_a_card(user_a_client):
    """A card belonging to user_a, returned as the raw JSON dict."""
    board = user_a_client.get("/api/boards").json()
    col = board["columns"][0]
    resp = user_a_client.post(
        f"/api/boards/{board['id']}/columns/{col['id']}/cards",
        json={"title": "User A card", "description": "owned by A"},
    )
    assert resp.status_code == 200
    return resp.json()


@pytest.fixture(scope="module")
def user_a_column(user_a_client):
    """First column belonging to user_a's board."""
    board = user_a_client.get("/api/boards").json()
    return board["columns"][0]


# ---------------------------------------------------------------------------
# PATCH /api/cards/{card_id}
# ---------------------------------------------------------------------------

def test_update_other_users_card_is_forbidden(user_b_client, user_a_card):
    resp = user_b_client.patch(
        f"/api/cards/{user_a_card['id']}",
        json={"title": "Hijacked"},
    )
    assert resp.status_code == 403


def test_update_own_card_succeeds(user_a_client, user_a_card):
    resp = user_a_client.patch(
        f"/api/cards/{user_a_card['id']}",
        json={"title": "Updated by A"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated by A"


# ---------------------------------------------------------------------------
# DELETE /api/cards/{card_id}
# ---------------------------------------------------------------------------

def test_delete_other_users_card_is_forbidden(user_b_client, user_a_card):
    resp = user_b_client.delete(f"/api/cards/{user_a_card['id']}")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# PUT /api/cards/{card_id}/move
# ---------------------------------------------------------------------------

def test_move_other_users_card_is_forbidden(user_b_client, user_a_card, user_a_column):
    resp = user_b_client.put(
        f"/api/cards/{user_a_card['id']}/move",
        json={"columnId": user_a_column["id"], "position": 0},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# PATCH /api/columns/{column_id}
# ---------------------------------------------------------------------------

def test_rename_other_users_column_is_forbidden(user_b_client, user_a_column):
    resp = user_b_client.patch(
        f"/api/columns/{user_a_column['id']}",
        json={"title": "Hijacked column"},
    )
    assert resp.status_code == 403


def test_rename_own_column_succeeds(user_a_client, user_a_column):
    resp = user_a_client.patch(
        f"/api/columns/{user_a_column['id']}",
        json={"title": "Renamed by A"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Renamed by A"


# ---------------------------------------------------------------------------
# Moving a card to another user's column is forbidden
# ---------------------------------------------------------------------------

def test_move_card_to_other_users_column_is_forbidden(user_a_client, user_a_card, user_b_client):
    """User A cannot move their own card into user B's column."""
    b_board = user_b_client.get("/api/boards").json()
    b_col = b_board["columns"][0]

    resp = user_a_client.put(
        f"/api/cards/{user_a_card['id']}/move",
        json={"columnId": b_col["id"], "position": 0},
    )
    assert resp.status_code == 404
