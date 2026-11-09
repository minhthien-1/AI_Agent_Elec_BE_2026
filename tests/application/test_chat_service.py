import uuid

import pytest

from application.chat_service import ChatApplicationError, ChatService


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


def test_send_message_returns_reply_and_records_trace():
    generator = FakeGenerator()
    recorder = FakeTraceRecorder()
    service = ChatService(generator, recorder)

    reply = service.send_message("  hỏi về máy giặt  ")

    assert reply.answer == "answer"
    assert reply.trace_id == str(recorder.trace_id)
    assert reply.duration_ms >= 0
    assert "Câu hỏi người dùng: hỏi về máy giặt" in generator.prompt
    assert recorder.steps[0]["input_data"]["message"] == "hỏi về máy giặt"
    assert recorder.status == "success"


def test_llm_failure_is_recorded_and_reported():
    generator = FakeGenerator(error=RuntimeError("LLM unavailable"))
    recorder = FakeTraceRecorder()
    service = ChatService(generator, recorder)

    with pytest.raises(ChatApplicationError) as error:
        service.send_message("question")

    assert error.value.kind == "llm_failed"
    assert error.value.trace_id == str(recorder.trace_id)
    assert recorder.status == "failed"
    assert recorder.steps[0]["output_data"]["error_type"] == "RuntimeError"


def test_trace_failure_is_reported_after_successful_generation():
    generator = FakeGenerator()
    recorder = FakeTraceRecorder(fail_on="finish_trace")
    service = ChatService(generator, recorder)

    with pytest.raises(ChatApplicationError) as error:
        service.send_message("question")

    assert error.value.kind == "trace_save_failed"
    assert error.value.trace_id == str(recorder.trace_id)
