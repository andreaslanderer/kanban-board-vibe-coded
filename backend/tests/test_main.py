def test_read_root_serves_static(test_client):
    response = test_client.get("/")
    assert response.status_code == 200
    assert "Static Export" in response.text


def test_api_hello(test_client):
    response = test_client.get("/api/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "Backend is working"}


def test_auth_login_success(test_client):
    response = test_client.post(
        "/api/auth/login", json={"username": "user", "password": "password"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["user"]["username"] == "user"


def test_auth_login_failure(test_client):
    response = test_client.post(
        "/api/auth/login", json={"username": "user", "password": "wrong"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is False


def test_get_board_returns_structure(test_client):
    response = test_client.get("/api/boards")
    assert response.status_code == 200
    body = response.json()
    assert "columns" in body
    assert isinstance(body["columns"], list)


def test_create_and_move_card(test_client):
    # Get current board and columns
    board = test_client.get("/api/boards").json()
    assert len(board["columns"]) >= 2

    col_from = board["columns"][0]
    col_to = board["columns"][1]

    # Create a new card in the first column
    card_resp = test_client.post(
        f"/api/boards/{board['id']}/columns/{col_from['id']}/cards",
        json={"title": "Test card", "description": "desc"},
    )
    assert card_resp.status_code == 200
    card = card_resp.json()

    # Move the card to the second column at position 0
    move_resp = test_client.put(
        f"/api/cards/{card['id']}/move",
        json={"columnId": col_to["id"], "position": 0},
    )
    assert move_resp.status_code == 200
    moved = move_resp.json()
    assert moved.get("column_id") == col_to["id"]


def test_update_and_delete_card(test_client):
    board = test_client.get("/api/boards").json()
    col = board["columns"][0]

    # create a card
    card_resp = test_client.post(
        f"/api/boards/{board['id']}/columns/{col['id']}/cards",
        json={"title": "Delete me", "description": "temp"},
    )
    card = card_resp.json()

    # update the card
    update_resp = test_client.patch(
        f"/api/cards/{card['id']}", json={"title": "Updated", "description": "new"}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Updated"

    # delete the card
    delete_resp = test_client.delete(f"/api/cards/{card['id']}")
    assert delete_resp.status_code == 204
