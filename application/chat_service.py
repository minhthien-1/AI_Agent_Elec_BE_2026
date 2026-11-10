import time
from typing import Literal

from application.ports import ChatGenerator, TraceRecorder
from application.results import ChatResult
from application.tools import ToolRegistry
from domain.chat import CHAT_SYSTEM_INSTRUCTIONS
from domain.routing import (
    CLARIFICATION_RESPONSE,
    EMERGENCY_RESPONSE,
    NO_DOCUMENTS_RESPONSE,
    Route,
    choose_route,
)


class ChatApplicationError(Exception):
    """Application failure that the API can translate to an HTTP response."""

    def __init__(
        self,
        message: str,
        trace_id: str,
        kind: Literal[
            "llm_failed",
            "retrieval_failed",
            "trace_save_failed",
        ],
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
        tools: ToolRegistry,
    ) -> None:
        self.generator = generator
        self.trace_recorder = trace_recorder
        self.tools = tools

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
        decision = choose_route(question)
        prompt: str | None = None
        model_name: str | None = None
        tool_name: str | None = None
        tool_arguments: dict[str, object] | None = None
        failed_operation: Literal["routing", "retrieval", "llm"] = "routing"
        try:
            if decision.route == Route.EMERGENCY:
                answer = EMERGENCY_RESPONSE
            elif decision.route == Route.ASK_CLARIFICATION:
                answer = CLARIFICATION_RESPONSE
            elif decision.route == Route.RETRIEVE_DOCUMENTS:
                failed_operation = "retrieval"
                # Tool registry thống nhất cách application gọi các năng lực của agent.
                tool_name = "search_manual"
                tool_arguments = {"query": question, "limit": 5}
                tool_result = self.tools.execute(tool_name, tool_arguments)
                if not tool_result.content.strip():
                    answer = NO_DOCUMENTS_RESPONSE
                else:
                    prompt = (
                        f"{CHAT_SYSTEM_INSTRUCTIONS}\n\n"
                        "Hãy trả lời câu hỏi dựa trên tài liệu tham khảo dưới đây. "
                        "Không tự bịa thông tin không có trong tài liệu. Nếu tài liệu "
                        "không đủ để kết luận, hãy nói rõ điều đó.\n\n"
                        f"Tài liệu tham khảo:\n{tool_result.content}\n\n"
                        f"Câu hỏi người dùng: {question}"
                    )
                    failed_operation = "llm"
                    model_name = self.generator.model_name
                    answer = self.generator.generate(prompt)
            else:
                prompt = (
                    f"{CHAT_SYSTEM_INSTRUCTIONS}\n\n"
                    f"Câu hỏi người dùng: {question}"
                )
                failed_operation = "llm"
                model_name = self.generator.model_name
                answer = self.generator.generate(prompt)
        except Exception as exc:
            try:
                self.trace_recorder.add_step(
                    trace_id=trace_id,
                    step_order=1,
                    step_name=decision.route.value,
                    input_data={
                        "message": question,
                        "route": decision.route.value,
                        "reason": decision.reason,
                        "tool_name": tool_name,
                        "tool_arguments": tool_arguments,
                        "model": model_name,
                        "prompt": prompt,
                    },
                    output_data={
                        "error_type": type(exc).__name__,
                        "failed_operation": failed_operation,
                    },
                    duration_ms=(time.perf_counter() - request_started) * 1000,
                )
                total_ms = (
                    time.perf_counter() - request_started
                ) * 1000
                self.trace_recorder.fail_trace(trace_id, total_ms)
            except Exception as trace_exc:
                raise ChatApplicationError(
                    message="Chat processing failed and trace recording failed.",
                    trace_id=trace_id_text,
                    kind="trace_save_failed",
                ) from trace_exc
            kind = (
                "retrieval_failed"
                if failed_operation == "retrieval"
                else "llm_failed"
            )
            message = (
                "Cannot retrieve reference documents."
                if failed_operation == "retrieval"
                else "Cannot get a response from Ollama."
            )
            raise ChatApplicationError(
                message=message,
                trace_id=trace_id_text,
                kind=kind,
            ) from exc

        try:
            self.trace_recorder.add_step(
                trace_id=trace_id,
                step_order=1,
                step_name=decision.route.value,
                input_data={
                    "message": question,
                    "route": decision.route.value,
                    "reason": decision.reason,
                    "tool_name": tool_name,
                    "tool_arguments": tool_arguments,
                    "model": model_name,
                    "prompt": prompt,
                },
                output_data={
                    "answer": answer,
                },
                duration_ms=(time.perf_counter() - request_started) * 1000,
            )
            total_ms = (
                time.perf_counter() - request_started
            ) * 1000
            self.trace_recorder.finish_trace(trace_id, total_ms)
        except Exception as exc:
            raise ChatApplicationError(
                message="Chat processing completed, but trace saving failed.",
                trace_id=trace_id_text,
                kind="trace_save_failed",
            ) from exc

        return ChatResult(
            answer=answer.strip(),
            trace_id=trace_id_text,
            duration_ms=round(total_ms, 2),
        )