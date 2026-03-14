import json
from fastapi.testclient import TestClient
from app.main import app, conversation_histories

def test_ai_chat_structured(monkeypatch):
    client = TestClient(app)
    # Patch OpenAI client to return a fixed structured response
    class DummyChoices:
        def __init__(self, content):
            self.message = type('msg', (), {'content': content})
    class DummyResponse:
        def __init__(self, content):
            self.choices = [DummyChoices(content)]
    class DummyCompletions:
        def create(self, **kwargs):
            return DummyResponse(json.dumps({
                "response": "Here is your answer.",
                "boardUpdates": {"cards": [], "columns": []}
            }))
    class DummyOpenAI:
        def __init__(self, *a, **k):
            self.chat = type('chat', (), {'completions': DummyCompletions()})()
    monkeypatch.setattr("app.main.OpenAI", DummyOpenAI)

    payload = {
        "question": "Add a new card to Backlog",
        "conversationHistory": []
    }
    response = client.post("/api/ai/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Here is your answer."
    assert "boardUpdates" in data
    # Check conversation history is updated
    user_id = 1
    assert conversation_histories[user_id][-1]["role"] == "assistant"
    assert conversation_histories[user_id][-1]["content"] == "Here is your answer."

def test_ai_chat_fallback(monkeypatch):
    client = TestClient(app)
    # Patch OpenAI client to return a non-JSON response
    class DummyChoices:
        def __init__(self, content):
            self.message = type('msg', (), {'content': content})
    class DummyResponse:
        def __init__(self, content):
            self.choices = [DummyChoices(content)]
    class DummyCompletions:
        def create(self, **kwargs):
            return DummyResponse("Just a plain text answer.")
    class DummyOpenAI:
        def __init__(self, *a, **k):
            self.chat = type('chat', (), {'completions': DummyCompletions()})()
    monkeypatch.setattr("app.main.OpenAI", DummyOpenAI)

    payload = {
        "question": "What is the status?",
        "conversationHistory": []
    }
    response = client.post("/api/ai/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Just a plain text answer."
    assert "boardUpdates" not in data or data["boardUpdates"] is None
    # Check conversation history is updated
    user_id = 1
    assert conversation_histories[user_id][-1]["role"] == "assistant"
    assert conversation_histories[user_id][-1]["content"] == "Just a plain text answer."
