import time
from typing import Literal

from application.ports import ChatGenerator, TraceRecorder
from application.results import ChatResult
from domain.chat import CHAT_SYSTEM_INSTRUCTIONS


class ChatApplicationError(Exception):
    """Application failure that the API can translate to an HTTP response."""

    def __init__(
        self,
        message: str,
        trace_id: str,
        kind: Literal["llm_failed", "trace_save_failed"],
    ):
        super().__init__(message)
        self.message = message
        self.trace_id = trace_id
        self.kind = kind


class ChatService:
    """Run one chat request using application ports."""

    def __init__(
        self,
        generator: ChatGenerator,
        trace_recorder: TraceRecorder,
    ) -> None:
        self.generator = generator
        self.trace_recorder = trace_recorder

    def send_message(
        self,
        message: str,
    ) -> ChatResult:
        question = message.strip()

        if not question:
            raise ValueError("Message cannot be empty")

        request_started = time.perf_counter()
        trace_id = self.trace_recorder.start_trace()
        trace_id_text = str(trace_id)
        prompt = (
            f"{CHAT_SYSTEM_INSTRUCTIONS}\n\n"
            f"Câu hỏi người dùng: {question}"
        )
        model_name = self.generator.model_name
        llm_started = time.perf_counter()

        try:
            answer = self.generator.generate(prompt)
        except Exception as exc:
            llm_duration_ms = (
                time.perf_counter() - llm_started
            ) * 1000

            try:
                self.trace_recorder.add_step(
                    trace_id=trace_id,
                    step_order=1,
                    step_name="ollama_generate",
                    input_data={
                        "message": question,
                        "model": model_name,
                    },
                    output_data={
                        "error_type": type(exc).__name__,
                        "message": "LLM call failed",
                    },
                    duration_ms=llm_duration_ms,
                )
                total_ms = (
                    time.perf_counter() - request_started
                ) * 1000
                self.trace_recorder.fail_trace(trace_id, total_ms)
            except Exception as trace_exc:
                raise ChatApplicationError(
                    message="LLM failed and trace recording failed.",
                    trace_id=trace_id_text,
                    kind="trace_save_failed",
                ) from trace_exc
            raise ChatApplicationError(
                message="Cannot get a response from Ollama.",
                trace_id=trace_id_text,
                kind="llm_failed",
            ) from exc

        llm_duration_ms = (
            time.perf_counter() - llm_started
        ) * 1000

        try:
            self.trace_recorder.add_step(
                trace_id=trace_id,
                step_order=1,
                step_name="ollama_generate",
                input_data={
                    "message": question,
                    "prompt": prompt,
                    "model": model_name,
                },
                output_data={
                    "answer": answer,
                },
                duration_ms=llm_duration_ms,
            )
            total_ms = (
                time.perf_counter() - request_started
            ) * 1000
            self.trace_recorder.finish_trace(trace_id, total_ms)
        except Exception as exc:
            raise ChatApplicationError(
                message="LLM responded, but trace saving failed.",
                trace_id=trace_id_text,
                kind="trace_save_failed",
            ) from exc

        return ChatResult(
            answer=answer.strip(),
            trace_id=trace_id_text,
            duration_ms=round(total_ms, 2),
        )