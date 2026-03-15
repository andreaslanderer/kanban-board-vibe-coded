import os


def test_read_root_serves_static(test_client):
    response = test_client.get("/")
    assert response.status_code == 200
    assert "Static Export" in response.text


def test_api_hello(test_client):
    response = test_client.get("/api/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "Backend is working"}


# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------

def test_protected_endpoint_requires_auth():
    """Requests without a session cookie must receive 401."""
    from app.main import app
    from fastapi.testclient import TestClient

    with TestClient(app, cookies={}) as fresh_client:
        assert fresh_client.get("/api/boards").status_code == 401
        assert fresh_client.post("/api/ai/chat", json={"question": "hi"}).status_code == 401


# ---------------------------------------------------------------------------
# Board & card tests (authenticated)
# ---------------------------------------------------------------------------

def test_get_board_returns_structure(auth_client):
    response = auth_client.get("/api/boards")
    assert response.status_code == 200
    body = response.json()
    assert "columns" in body
    assert isinstance(body["columns"], list)
    assert len(body["columns"]) == 5


def test_create_and_move_card(auth_client):
    board = auth_client.get("/api/boards").json()
    assert len(board["columns"]) >= 2
    col_from = board["columns"][0]
    col_to = board["columns"][1]

    card_resp = auth_client.post(
        f"/api/boards/{board['id']}/columns/{col_from['id']}/cards",
        json={"title": "Test card", "description": "desc"},
    )
    assert card_resp.status_code == 200
    card = card_resp.json()

    move_resp = auth_client.put(
        f"/api/cards/{card['id']}/move",
        json={"columnId": col_to["id"], "position": 0},
    )
    assert move_resp.status_code == 200
    assert move_resp.json()["column_id"] == col_to["id"]


def test_update_and_delete_card(auth_client):
    board = auth_client.get("/api/boards").json()
    col = board["columns"][0]

    card_resp = auth_client.post(
        f"/api/boards/{board['id']}/columns/{col['id']}/cards",
        json={"title": "Delete me", "description": "temp"},
    )
    card = card_resp.json()

    update_resp = auth_client.patch(
        f"/api/cards/{card['id']}", json={"title": "Updated", "description": "new"}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Updated"

    delete_resp = auth_client.delete(f"/api/cards/{card['id']}")
    assert delete_resp.status_code == 204


# ---------------------------------------------------------------------------
# AI test endpoint
# ---------------------------------------------------------------------------

def test_ai_test_success(test_client, mocker):
    mock_client = mocker.Mock()
    mock_response = mocker.Mock()
    mock_choice = mocker.Mock()
    mock_choice.message.content = "4"
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    mocker.patch("app.main.OpenAI", return_value=mock_client)
    mocker.patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"})

    response = test_client.get("/api/ai/test")
    assert response.status_code == 200
    assert response.json() == {"response": "4"}


def test_ai_test_no_api_key(test_client, mocker):
    mocker.patch.dict(os.environ, {}, clear=True)
    response = test_client.get("/api/ai/test")
    assert response.status_code == 500
    assert "API key not configured" in response.json()["detail"]
