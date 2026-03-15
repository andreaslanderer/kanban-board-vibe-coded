import json

from app.main import conversation_histories


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

    response = auth_client.post(
        "/api/ai/chat",
        json={"question": "Add a new card to Backlog", "conversationHistory": []},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Here is your answer."
    assert "boardUpdates" in data


def test_ai_chat_fallback(auth_client, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
    monkeypatch.setattr("app.main.OpenAI", _dummy_openai("Just a plain text answer."))

    response = auth_client.post(
        "/api/ai/chat",
        json={"question": "What is the status?", "conversationHistory": []},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Just a plain text answer."
    assert data.get("boardUpdates") is None


def test_ai_chat_no_api_key(auth_client, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    response = auth_client.post("/api/ai/chat", json={"question": "test"})
    assert response.status_code == 500
    assert "API key" in response.json()["detail"]


def test_ai_chat_conversation_history_grows(auth_client, monkeypatch):
    """Each exchange appends both user and assistant messages to the history."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
    monkeypatch.setattr(
        "app.main.OpenAI",
        _dummy_openai(json.dumps({"response": "Got it.", "boardUpdates": None})),
    )

    conversation_histories.clear()

    auth_client.post("/api/ai/chat", json={"question": "First message"})
    auth_client.post("/api/ai/chat", json={"question": "Second message"})

    assert len(conversation_histories) > 0
    history = next(iter(conversation_histories.values()))
    assert len(history) >= 4  # 2 user + 2 assistant turns
    roles = [m["role"] for m in history[-4:]]
    assert roles == ["user", "assistant", "user", "assistant"]
