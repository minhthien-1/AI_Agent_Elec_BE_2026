import time
from typing import Literal

from application.ports import AnswerReviewer, ChatGenerator, TraceRecorder
from application.results import ChatResult
from application.tools import ToolRegistry
from domain.answer_review import UNSAFE_ANSWER_RESPONSE
from domain.chat import CHAT_SYSTEM_INSTRUCTIONS
from domain.routing import (
    EMERGENCY_RESPONSE,
    NO_DOCUMENTS_RESPONSE,
    REFUSAL_RESPONSE,
    Route,
    clarification_fields_for,
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
            "tool_failed",
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
        reviewer: AnswerReviewer,
    ) -> None:
        self.generator = generator
        self.trace_recorder = trace_recorder
        self.tools = tools
        # P4-2: reviewer là module riêng, chạy sau khi có câu trả lời và có quyền chặn.
        self.reviewer = reviewer

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
        failed_operation: Literal[
            "routing",
            "clarification",
            "retrieval",
            "llm",
        ] = "routing"
        # P4-2: mặc định MỌI câu trả lời đều phải qua reviewer, kể cả output của tool mới
        # thêm sau này. Chỉ các câu cố định viết sẵn trong domain/ (đã được test) mới được
        # đánh dấu bỏ qua, để reviewer không chặn nhầm cảnh báo hoặc từ chối an toàn.
        needs_review = True
        try:
            if decision.route == Route.EMERGENCY:
                answer = EMERGENCY_RESPONSE
                needs_review = False
            elif decision.route == Route.REFUSE:
                # P4-3: yêu cầu thao tác rủi ro bị từ chối trước khi gọi LLM hoặc RAG.
                answer = REFUSAL_RESPONSE
                needs_review = False
            elif decision.route == Route.ASK_CLARIFICATION:
                # Router đã xác định request còn thiếu ngữ cảnh; tool tạo câu hỏi cụ thể.
                failed_operation = "clarification"
                tool_name = "ask_clarification"
                tool_arguments = {
                    # Chỉ hỏi những thông tin chưa nhận diện được từ request hiện tại.
                    "missing_fields": clarification_fields_for(question),
                }
                tool_result = self.tools.execute(tool_name, tool_arguments)
                answer = tool_result.content
            elif decision.route == Route.RETRIEVE_DOCUMENTS:
                failed_operation = "retrieval"
                # Tool registry thống nhất cách application gọi các năng lực của agent.
                tool_name = "search_manual"
                tool_arguments = {"query": question, "limit": 5}
                tool_result = self.tools.execute(tool_name, tool_arguments)
                if not tool_result.content.strip():
                    answer = NO_DOCUMENTS_RESPONSE
                    needs_review = False
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
                else (
                    "tool_failed"
                    if failed_operation == "clarification"
                    else "llm_failed"
                )
            )
            message = (
                "Cannot retrieve reference documents."
                if failed_operation == "retrieval"
                else (
                    "Cannot create a clarification question."
                    if failed_operation == "clarification"
                    else "Cannot get a response from Ollama."
                )
            )
            raise ChatApplicationError(
                message=message,
                trace_id=trace_id_text,
                kind=kind,
            ) from exc

        # P4-2: một cửa kiểm duyệt duy nhất, đặt SAU mọi nhánh và TRƯỚC khi trả kết quả.
        # Đặt ở đây (không rải vào từng nhánh) để không nhánh nào có thể bỏ sót review.
        generated_answer = answer
        review_started = time.perf_counter()
        review_output: dict[str, object]
        if not needs_review:
            review_output = {"status": "skipped", "reason": "trusted_template"}
        else:
            try:
                review = self.reviewer.review(question, answer)
            except Exception as exc:
                # Fail-closed: reviewer lỗi thì không trả câu chưa được kiểm duyệt,
                # thay bằng cảnh báo. Không ném lỗi ra API vì người dùng vẫn nhận được
                # một phản hồi an toàn; lỗi được ghi lại trong trace để điều tra.
                answer = UNSAFE_ANSWER_RESPONSE
                review_output = {
                    "status": "error",
                    "reason": "reviewer_failed_closed",
                    "error_type": type(exc).__name__,
                    "blocked_answer": generated_answer,
                }
            else:
                if review.allowed:
                    review_output = {"status": "allowed", "reason": review.reason}
                else:
                    answer = UNSAFE_ANSWER_RESPONSE
                    review_output = {
                        "status": "blocked",
                        "reason": review.reason,
                        "matched_rules": list(review.matched_rules),
                        # Lưu câu gốc bị chặn để sau này rà soát các trường hợp chặn nhầm.
                        "blocked_answer": generated_answer,
                    }
        review_output["final_answer"] = answer
        review_ms = (time.perf_counter() - review_started) * 1000

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
                    # Step 1 giữ câu trả lời do nhánh route tạo ra (trước kiểm duyệt).
                    "answer": generated_answer,
                },
                duration_ms=(time.perf_counter() - request_started) * 1000,
            )
            # P4-2: step riêng cho kiểm duyệt để truy vấn trace dễ thấy câu nào bị chặn.
            self.trace_recorder.add_step(
                trace_id=trace_id,
                step_order=2,
                step_name="answer_review",
                input_data={
                    "route": decision.route.value,
                    "needs_review": needs_review,
                },
                output_data=review_output,
                duration_ms=review_ms,
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