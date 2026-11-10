from fastapi.testclient import TestClient

from api.dependencies import get_chat_service
from api.main import app
from application.chat_service import ChatApplicationError
from application.results import ChatResult


client = TestClient(app)


def test_chat_endpoint_returns_application_result():
    class FakeChatService:
        def send_message(self, message: str) -> ChatResult:
            assert message == "Tủ lạnh không lạnh"
            return ChatResult(
                answer="Hãy kiểm tra nguồn điện.",
                trace_id="trace-123",
                duration_ms=15.0,
            )

    app.dependency_overrides[get_chat_service] = FakeChatService
    try:
        response = client.post(
            "/chat",
            json={"message": " Tủ lạnh không lạnh "},
        )
    finally:
        app.dependency_overrides.pop(get_chat_service, None)

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Hãy kiểm tra nguồn điện.",
        "trace_id": "trace-123",
        "duration_ms": 15.0,
    }


def test_chat_endpoint_maps_application_error_to_http_status():
    class FailedChatService:
        def send_message(self, message: str) -> ChatResult:
            raise ChatApplicationError(
                message="Cannot get a response from Ollama.",
                trace_id="trace-456",
                kind="llm_failed",
            )

    app.dependency_overrides[get_chat_service] = FailedChatService
    try:
        response = client.post("/chat", json={"message": "test"})
    finally:
        app.dependency_overrides.pop(get_chat_service, None)

    assert response.status_code == 502
    assert response.json()["detail"] == {
        "message": "Cannot get a response from Ollama.",
        "trace_id": "trace-456",
    }


def test_chat_endpoint_maps_retrieval_error_to_bad_gateway():
    class FailedChatService:
        def send_message(self, message: str) -> ChatResult:
            raise ChatApplicationError(
                message="Cannot retrieve reference documents.",
                trace_id="trace-789",
                kind="retrieval_failed",
            )

    app.dependency_overrides[get_chat_service] = FailedChatService
    try:
        response = client.post(
            "/chat",
            json={"message": "Máy giặt không lên nguồn"},
        )
    finally:
        app.dependency_overrides.pop(get_chat_service, None)

    assert response.status_code == 502
