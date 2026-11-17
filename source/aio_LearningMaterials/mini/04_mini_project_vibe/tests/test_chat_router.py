"""Gemini를 실제 호출하지 않고 Chat Router를 테스트합니다."""

from app.routers import chat_router
from app.schemas.chat_schema import ChatResponse
from app.services.chat_service import ChatConfigurationError, ChatServiceError


def test_chat_success(client, monkeypatch):
    monkeypatch.setattr(
        chat_router,
        "generate_chat_response",
        lambda message: ChatResponse(answer="테스트 응답", model="test-model"),
    )
    response = client.post("/chat/gemini", json={"message": "안녕하세요"})
    assert response.status_code == 200
    assert response.json()["data"]["answer"] == "테스트 응답"


def test_empty_chat_message_returns_422(client):
    assert client.post("/chat/gemini", json={"message": " "}).status_code == 422


def test_missing_chat_configuration_returns_500(client, monkeypatch):
    def missing_configuration(_message):
        raise ChatConfigurationError

    monkeypatch.setattr(chat_router, "generate_chat_response", missing_configuration)
    assert client.post("/chat/gemini", json={"message": "안녕하세요"}).status_code == 500


def test_chat_external_error_returns_502(client, monkeypatch):
    def external_error(_message):
        raise ChatServiceError

    monkeypatch.setattr(chat_router, "generate_chat_response", external_error)
    assert client.post("/chat/gemini", json={"message": "안녕하세요"}).status_code == 502
