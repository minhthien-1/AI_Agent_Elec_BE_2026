import uuid

import pytest

from application.ports import RetrievedDocument
from application.chat_service import ChatApplicationError, ChatService
from application.tools import ToolRegistry
from domain.answer_review import (
    UNSAFE_ANSWER_RESPONSE,
    ReviewDecision,
    RuleBasedAnswerReviewer,
)
from domain.routing import (
    EMERGENCY_RESPONSE,
    NO_DOCUMENTS_RESPONSE,
    Route,
)
from infrastructure.tools.ask_clarification import AskClarificationTool
from infrastructure.tools.search_manual import SearchManualTool


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

    def finish_trace(self, trace_id: uuid.UUID, _total_ms: float) -> None:
        if self.fail_on == "finish_trace":
            raise RuntimeError("trace finish failed")
        assert trace_id == self.trace_id
        assert _total_ms >= 0
        self.status = "success"

    def fail_trace(self, trace_id: uuid.UUID, _total_ms: float) -> None:
        if self.fail_on == "fail_trace":
            raise RuntimeError("trace failure write failed")
        assert trace_id == self.trace_id
        assert _total_ms >= 0
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


class SpyReviewer:
    """Ghi lại các câu được gửi tới reviewer; có thể giả lập lỗi để kiểm tra fail-closed."""

    def __init__(self, error: Exception | None = None):
        self.error = error
        self.reviewed: list[str] = []
        self._inner = RuleBasedAnswerReviewer()

    def review(self, question: str, answer: str) -> ReviewDecision:
        self.reviewed.append(answer)
        if self.error is not None:
            raise self.error
        return self._inner.review(question, answer)


def create_chat_service(
    generator: FakeGenerator,
    recorder: FakeTraceRecorder,
    retriever: FakeDocumentRetriever,
    reviewer: SpyReviewer | None = None,
) -> ChatService:
    return ChatService(
        generator,
        recorder,
        ToolRegistry(
            [
                SearchManualTool(retriever),
                AskClarificationTool(),
            ]
        ),
        reviewer or SpyReviewer(),
    )


def review_step(recorder: FakeTraceRecorder) -> dict:
    return next(s for s in recorder.steps if s["step_name"] == "answer_review")


def test_send_message_returns_reply_and_records_trace():
    generator = FakeGenerator()
    recorder = FakeTraceRecorder()
    retriever = FakeDocumentRetriever()
    service = create_chat_service(generator, recorder, retriever)

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
    service = create_chat_service(generator, recorder, FakeDocumentRetriever())

    with pytest.raises(ChatApplicationError) as error:
        service.send_message("Điện là gì?")

    assert error.value.kind == "llm_failed"
    assert error.value.trace_id == str(recorder.trace_id)
    assert recorder.status == "failed"
    assert recorder.steps[0]["output_data"]["error_type"] == "RuntimeError"


def test_trace_failure_is_reported_after_successful_generation():
    generator = FakeGenerator()
    recorder = FakeTraceRecorder(fail_on="finish_trace")
    service = create_chat_service(generator, recorder, FakeDocumentRetriever())

    with pytest.raises(ChatApplicationError) as error:
        service.send_message("Điện là gì?")

    assert error.value.kind == "trace_save_failed"
    assert error.value.trace_id == str(recorder.trace_id)


def test_emergency_route_returns_fixed_warning_without_llm_or_retrieval():
    generator = FakeGenerator()
    recorder = FakeTraceRecorder()
    retriever = FakeDocumentRetriever()
    service = create_chat_service(generator, recorder, retriever)

    reply = service.send_message("Máy giặt có mùi khét")

    assert reply.answer == EMERGENCY_RESPONSE
    assert generator.prompt is None
    assert retriever.queries == []
    assert recorder.steps[0]["input_data"]["route"] == Route.EMERGENCY


@pytest.mark.parametrize(
    "message",
    (
        "Nước vào ổ cắm",
        "Tôi đang sửa máy giặt khi chưa ngắt nguồn",
        "Tủ lạnh có mùi khét",
    ),
)
def test_all_hard_safety_signals_bypass_llm_and_rag(message: str):
    generator = FakeGenerator()
    recorder = FakeTraceRecorder()
    retriever = FakeDocumentRetriever()
    service = create_chat_service(generator, recorder, retriever)

    reply = service.send_message(message)

    assert reply.answer == EMERGENCY_RESPONSE
    assert generator.prompt is None
    assert retriever.queries == []
    assert recorder.steps[0]["input_data"]["route"] == Route.EMERGENCY


def test_ambiguous_route_asks_for_details_without_llm_or_retrieval():
    generator = FakeGenerator()
    recorder = FakeTraceRecorder()
    retriever = FakeDocumentRetriever()
    service = create_chat_service(generator, recorder, retriever)

    reply = service.send_message("Giúp tôi")

    assert "thiết bị nào" in reply.answer
    assert "biểu hiện cụ thể" in reply.answer
    assert generator.prompt is None
    assert retriever.queries == []
    assert recorder.steps[0]["input_data"]["route"] == Route.ASK_CLARIFICATION
    assert recorder.steps[0]["input_data"]["tool_name"] == "ask_clarification"
    assert recorder.steps[0]["input_data"]["tool_arguments"] == {
        "missing_fields": ["device", "symptoms"],
    }


def test_clarification_asks_only_for_symptoms_when_device_is_known():
    generator = FakeGenerator()
    recorder = FakeTraceRecorder()
    retriever = FakeDocumentRetriever()
    service = create_chat_service(generator, recorder, retriever)

    reply = service.send_message("Máy giặt")

    assert reply.answer == "Thiết bị đang có biểu hiện cụ thể như thế nào?"
    assert recorder.steps[0]["input_data"]["tool_arguments"] == {
        "missing_fields": ["symptoms"],
    }


def test_retrieval_route_uses_context_in_llm_prompt():
    generator = FakeGenerator()
    recorder = FakeTraceRecorder()
    retriever = FakeDocumentRetriever(
        [RetrievedDocument(content="Tài liệu: kiểm tra dây nguồn.", source="washer.pdf")]
    )
    service = create_chat_service(generator, recorder, retriever)

    reply = service.send_message("Máy giặt không lên nguồn")

    assert reply.answer == "answer"
    assert retriever.queries == ["Máy giặt không lên nguồn"]
    assert "kiểm tra dây nguồn" in generator.prompt
    assert "washer.pdf" in generator.prompt
    assert recorder.steps[0]["input_data"]["route"] == Route.RETRIEVE_DOCUMENTS
    assert recorder.steps[0]["input_data"]["tool_name"] == "search_manual"
    assert recorder.steps[0]["input_data"]["tool_arguments"] == {
        "query": "Máy giặt không lên nguồn",
        "limit": 5,
    }


def test_retrieval_without_results_asks_for_model_instead_of_guessing():
    generator = FakeGenerator()
    recorder = FakeTraceRecorder()
    retriever = FakeDocumentRetriever()
    service = create_chat_service(generator, recorder, retriever)

    reply = service.send_message("Máy giặt không lên nguồn")

    assert reply.answer == NO_DOCUMENTS_RESPONSE
    assert generator.prompt is None


def test_retrieval_error_is_reported_and_trace_is_failed():
    generator = FakeGenerator()
    recorder = FakeTraceRecorder()
    retriever = FakeDocumentRetriever(error=RuntimeError("database unavailable"))
    service = create_chat_service(generator, recorder, retriever)

    with pytest.raises(ChatApplicationError) as error:
        service.send_message("Máy giặt không lên nguồn")

    assert error.value.kind == "retrieval_failed"
    assert recorder.status == "failed"


# ---- P4-2: bộ kiểm duyệt độc lập ----


def test_unsafe_llm_answer_is_blocked_and_original_kept_in_trace():
    unsafe = "Bạn rút phích cắm rồi tháo vỏ máy và xả tụ bằng tua vít."
    generator = FakeGenerator(answer=unsafe)
    recorder = FakeTraceRecorder()
    service = create_chat_service(generator, recorder, FakeDocumentRetriever())

    reply = service.send_message("Điện là gì?")

    assert reply.answer == UNSAFE_ANSWER_RESPONSE
    # LLM vẫn được gọi: reviewer chạy SAU khi sinh, không thay thế bước sinh.
    assert generator.prompt is not None
    assert recorder.steps[0]["output_data"]["answer"] == unsafe
    step = review_step(recorder)
    assert step["step_order"] == 2
    assert step["output_data"]["status"] == "blocked"
    assert step["output_data"]["blocked_answer"] == unsafe
    assert step["output_data"]["final_answer"] == UNSAFE_ANSWER_RESPONSE
    assert "high_energy_component" in step["output_data"]["matched_rules"]
    assert recorder.status == "success"


def test_unsafe_rag_answer_is_blocked():
    generator = FakeGenerator(answer="Hãy nối tắt cầu chì để máy chạy lại.")
    recorder = FakeTraceRecorder()
    retriever = FakeDocumentRetriever(
        [RetrievedDocument(content="Tài liệu máy giặt.", source="washer.pdf")]
    )
    service = create_chat_service(generator, recorder, retriever)

    reply = service.send_message("Máy giặt không lên nguồn")

    assert reply.answer == UNSAFE_ANSWER_RESPONSE
    assert review_step(recorder)["output_data"]["status"] == "blocked"


def test_safe_llm_answer_passes_review_unchanged():
    reviewer = SpyReviewer()
    recorder = FakeTraceRecorder()
    service = create_chat_service(
        FakeGenerator(answer="Rút phích cắm rồi vệ sinh lưới lọc."),
        recorder,
        FakeDocumentRetriever(),
        reviewer,
    )

    reply = service.send_message("Điện là gì?")

    assert reply.answer == "Rút phích cắm rồi vệ sinh lưới lọc."
    assert reviewer.reviewed == ["Rút phích cắm rồi vệ sinh lưới lọc."]
    assert review_step(recorder)["output_data"]["status"] == "allowed"


@pytest.mark.parametrize(
    ("message", "expected"),
    (
        ("Máy giặt có mùi khét", EMERGENCY_RESPONSE),
        ("Máy giặt không lên nguồn", NO_DOCUMENTS_RESPONSE),
    ),
)
def test_trusted_templates_skip_review(message: str, expected: str):
    reviewer = SpyReviewer()
    recorder = FakeTraceRecorder()
    service = create_chat_service(
        FakeGenerator(), recorder, FakeDocumentRetriever(), reviewer
    )

    reply = service.send_message(message)

    assert reply.answer == expected
    assert reviewer.reviewed == []
    step = review_step(recorder)
    assert step["output_data"]["status"] == "skipped"
    assert step["output_data"]["reason"] == "trusted_template"


def test_tool_output_is_reviewed_by_default():
    # ask_clarification là tool, không phải template trong domain → vẫn phải review.
    reviewer = SpyReviewer()
    service = create_chat_service(
        FakeGenerator(), FakeTraceRecorder(), FakeDocumentRetriever(), reviewer
    )

    service.send_message("Giúp tôi")

    assert len(reviewer.reviewed) == 1


def test_reviewer_error_fails_closed():
    recorder = FakeTraceRecorder()
    service = create_chat_service(
        FakeGenerator(answer="Một câu trả lời bình thường."),
        recorder,
        FakeDocumentRetriever(),
        SpyReviewer(error=RuntimeError("reviewer crashed")),
    )

    reply = service.send_message("Điện là gì?")

    assert reply.answer == UNSAFE_ANSWER_RESPONSE
    step = review_step(recorder)
    assert step["output_data"]["status"] == "error"
    assert step["output_data"]["error_type"] == "RuntimeError"
    assert step["output_data"]["blocked_answer"] == "Một câu trả lời bình thường."
    assert recorder.status == "success"
