import json


def _dummy_openai(response_content: str):
    """Return a DummyOpenAI class whose completions return response_content."""

    class DummyMessage:
        def __init__(self, content):
            self.content = content

    class DummyChoice:
        def __init__(self, content):
            self.message = DummyMessage(content)

    class DummyResponse:
        def __init__(self, content):
            self.choices = [DummyChoice(content)]

    class DummyCompletions:
        def __init__(self, content):
            self._content = content

        def create(self, **kwargs):
            return DummyResponse(self._content)

    class DummyOpenAI:
        def __init__(self, *a, **k):
            self.chat = type("chat", (), {"completions": DummyCompletions(response_content)})()

    return DummyOpenAI


def test_ai_chat_structured(auth_client, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
    monkeypatch.setattr(
        "app.main.OpenAI",
        _dummy_openai(json.dumps({"response": "Here is your answer.", "boardUpdates": {"cards": [], "columns": []}})),
    )

    response = auth_client.post("/api/ai/chat", json={"question": "Add a new card to Backlog"})
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Here is your answer."
    assert "boardUpdates" in data


def test_ai_chat_fallback(auth_client, monkeypatch):
    """Plain-text (non-JSON) AI response falls back gracefully."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
    monkeypatch.setattr("app.main.OpenAI", _dummy_openai("Just a plain text answer."))

    response = auth_client.post("/api/ai/chat", json={"question": "What is the status?"})
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Just a plain text answer."
    assert data.get("boardUpdates") is None


def test_ai_chat_invalid_schema_falls_back(auth_client, monkeypatch):
    """Valid JSON that fails schema validation falls back to plain text response."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
    # JSON is valid but missing the required 'response' field
    monkeypatch.setattr("app.main.OpenAI", _dummy_openai(json.dumps({"wrong_field": "value"})))

    response = auth_client.post("/api/ai/chat", json={"question": "test"})
    assert response.status_code == 200
    data = response.json()
    # Falls back: raw AI content becomes the response
    assert data["response"] == json.dumps({"wrong_field": "value"})
    assert data.get("boardUpdates") is None


def test_ai_chat_markdown_fences_stripped(auth_client, monkeypatch):
    """AI response wrapped in markdown code fences is parsed correctly."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
    inner = json.dumps({"response": "Stripped!", "boardUpdates": None})
    monkeypatch.setattr("app.main.OpenAI", _dummy_openai(f"```json\n{inner}\n```"))

    response = auth_client.post("/api/ai/chat", json={"question": "test"})
    assert response.status_code == 200
    assert response.json()["response"] == "Stripped!"


def test_ai_chat_no_api_key(auth_client, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    response = auth_client.post("/api/ai/chat", json={"question": "test"})
    assert response.status_code == 500
    assert "API key" in response.json()["detail"]


def test_ai_chat_conversation_history_grows(auth_client, monkeypatch):
    """Each exchange appends both user and assistant messages; GET /api/ai/history reflects this."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
    monkeypatch.setattr(
        "app.main.OpenAI",
        _dummy_openai(json.dumps({"response": "Got it.", "boardUpdates": None})),
    )

    # Clear any existing history for this user first
    auth_client.delete("/api/ai/history")

    auth_client.post("/api/ai/chat", json={"question": "First message"})
    auth_client.post("/api/ai/chat", json={"question": "Second message"})


    history_resp = auth_client.get("/api/ai/history")
    assert history_resp.status_code == 200
    messages = history_resp.json()["messages"]
    assert len(messages) >= 4  # 2 user + 2 assistant turns
    roles = [m["role"] for m in messages[-4:]]
    assert roles == ["user", "assistant", "user", "assistant"]


def test_ai_history_clear(auth_client, monkeypatch):
    """DELETE /api/ai/history removes all messages for the current user."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
    monkeypatch.setattr(
        "app.main.OpenAI",
        _dummy_openai(json.dumps({"response": "OK", "boardUpdates": None})),
    )

    auth_client.post("/api/ai/chat", json={"question": "Seed a message"})


    # Confirm there is at least one message
    history_before = auth_client.get("/api/ai/history").json()["messages"]
    assert len(history_before) >= 1

    # Clear
    clear_resp = auth_client.delete("/api/ai/history")
    assert clear_resp.status_code == 204

    # Confirm empty
    history_after = auth_client.get("/api/ai/history").json()["messages"]
    assert history_after == []


def test_ai_history_requires_auth(monkeypatch):
    """GET and DELETE /api/ai/history return 401 without a session."""
    from app.main import app
    from fastapi.testclient import TestClient

    with TestClient(app, cookies={}) as fresh_client:
        assert fresh_client.get("/api/ai/history").status_code == 401
        assert fresh_client.delete("/api/ai/history").status_code == 401
