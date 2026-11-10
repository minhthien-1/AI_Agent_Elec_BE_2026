import uuid

import pytest

from application.ports import RetrievedDocument
from application.chat_service import ChatApplicationError, ChatService
from domain.routing import (
    CLARIFICATION_RESPONSE,
    EMERGENCY_RESPONSE,
    NO_DOCUMENTS_RESPONSE,
    Route,
)


class FakeGenerator:
    model_name = "test-model"

    def __init__(self, answer: str = "  answer  ", error: Exception | None = None):
        self.answer = answer
        self.error = error
        self.prompt = None

    def generate(self, prompt: str) -> str:
        self.prompt = prompt
        if self.error is not None:
            raise self.error
        return self.answer


class FakeTraceRecorder:
    def __init__(self, fail_on: str | None = None):
        self.trace_id = uuid.uuid4()
        self.fail_on = fail_on
        self.steps = []
        self.status = "running"

    def start_trace(self) -> uuid.UUID:
        return self.trace_id

    def add_step(self, **step) -> None:
        if self.fail_on == "add_step":
            raise RuntimeError("trace step write failed")
        self.steps.append(step)

    def finish_trace(self, trace_id: uuid.UUID, total_ms: float) -> None:
        if self.fail_on == "finish_trace":
            raise RuntimeError("trace finish failed")
        assert trace_id == self.trace_id
        self.status = "success"

    def fail_trace(self, trace_id: uuid.UUID, total_ms: float) -> None:
        if self.fail_on == "fail_trace":
            raise RuntimeError("trace failure write failed")
        assert trace_id == self.trace_id
        self.status = "failed"


class FakeDocumentRetriever:
    def __init__(
        self,
        documents: list[RetrievedDocument] | None = None,
        error: Exception | None = None,
    ):
        self.documents = documents or []
        self.error = error
        self.queries = []

    def retrieve(self, query: str, limit: int = 5) -> list[RetrievedDocument]:
        self.queries.append(query)
        if self.error is not None:
            raise self.error
        return self.documents[:limit]


def test_send_message_returns_reply_and_records_trace():
    generator = FakeGenerator()
    recorder = FakeTraceRecorder()
    retriever = FakeDocumentRetriever()
    service = ChatService(generator, recorder, retriever)

    reply = service.send_message("  Điện là gì?  ")

    assert reply.answer == "answer"
    assert reply.trace_id == str(recorder.trace_id)
    assert reply.duration_ms >= 0
    assert "Câu hỏi người dùng: Điện là gì?" in generator.prompt
    assert recorder.steps[0]["input_data"]["message"] == "Điện là gì?"
    assert recorder.steps[0]["input_data"]["route"] == Route.DIRECT_ANSWER
    assert recorder.status == "success"


def test_llm_failure_is_recorded_and_reported():
    generator = FakeGenerator(error=RuntimeError("LLM unavailable"))
    recorder = FakeTraceRecorder()
    service = ChatService(generator, recorder, FakeDocumentRetriever())

    with pytest.raises(ChatApplicationError) as error:
        service.send_message("Điện là gì?")

    assert error.value.kind == "llm_failed"
    assert error.value.trace_id == str(recorder.trace_id)
    assert recorder.status == "failed"
    assert recorder.steps[0]["output_data"]["error_type"] == "RuntimeError"


def test_trace_failure_is_reported_after_successful_generation():
    generator = FakeGenerator()
    recorder = FakeTraceRecorder(fail_on="finish_trace")
    service = ChatService(generator, recorder, FakeDocumentRetriever())

    with pytest.raises(ChatApplicationError) as error:
        service.send_message("Điện là gì?")

    assert error.value.kind == "trace_save_failed"
    assert error.value.trace_id == str(recorder.trace_id)


def test_emergency_route_returns_fixed_warning_without_llm_or_retrieval():
    generator = FakeGenerator()
    recorder = FakeTraceRecorder()
    retriever = FakeDocumentRetriever()
    service = ChatService(generator, recorder, retriever)

    reply = service.send_message("Máy giặt có mùi khét")

    assert reply.answer == EMERGENCY_RESPONSE
    assert generator.prompt is None
    assert retriever.queries == []
    assert recorder.steps[0]["input_data"]["route"] == Route.EMERGENCY


def test_ambiguous_route_asks_for_details_without_llm_or_retrieval():
    generator = FakeGenerator()
    recorder = FakeTraceRecorder()
    retriever = FakeDocumentRetriever()
    service = ChatService(generator, recorder, retriever)

    reply = service.send_message("Giúp tôi")

    assert reply.answer == CLARIFICATION_RESPONSE
    assert generator.prompt is None
    assert retriever.queries == []
    assert recorder.steps[0]["input_data"]["route"] == Route.ASK_CLARIFICATION


def test_retrieval_route_uses_context_in_llm_prompt():
    generator = FakeGenerator()
    recorder = FakeTraceRecorder()
    retriever = FakeDocumentRetriever(
        [RetrievedDocument(content="Tài liệu: kiểm tra dây nguồn.", source="washer.pdf")]
    )
    service = ChatService(generator, recorder, retriever)

    reply = service.send_message("Máy giặt không lên nguồn")

    assert reply.answer == "answer"
    assert retriever.queries == ["Máy giặt không lên nguồn"]
    assert "kiểm tra dây nguồn" in generator.prompt
    assert "washer.pdf" in generator.prompt
    assert recorder.steps[0]["input_data"]["route"] == Route.RETRIEVE_DOCUMENTS


def test_retrieval_without_results_asks_for_model_instead_of_guessing():
    generator = FakeGenerator()
    recorder = FakeTraceRecorder()
    retriever = FakeDocumentRetriever()
    service = ChatService(generator, recorder, retriever)

    reply = service.send_message("Máy giặt không lên nguồn")

    assert reply.answer == NO_DOCUMENTS_RESPONSE
    assert generator.prompt is None


def test_retrieval_error_is_reported_and_trace_is_failed():
    generator = FakeGenerator()
    recorder = FakeTraceRecorder()
    retriever = FakeDocumentRetriever(error=RuntimeError("database unavailable"))
    service = ChatService(generator, recorder, retriever)

    with pytest.raises(ChatApplicationError) as error:
        service.send_message("Máy giặt không lên nguồn")

    assert error.value.kind == "retrieval_failed"
    assert recorder.status == "failed"
