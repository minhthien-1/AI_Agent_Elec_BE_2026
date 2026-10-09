import time

from sqlalchemy.orm import Session

from llm.ollama_client import OllamaClient
from tools.trace_service import TraceService


class ChatServiceError(Exception):
    """Error raised while processing a chat request."""

    def __init__(
        self,
        message: str,
        trace_id: str,
        status_code: int,
    ):
        super().__init__(message)
        self.message = message
        self.trace_id = trace_id
        self.status_code = status_code


class ChatService:
    """Coordinate LLM generation and trace recording."""

    def __init__(self):
        self.trace_service = TraceService()

    def send_message(
        self,
        db: Session,
        message: str,
    ) -> dict:
        question = message.strip()

        if not question:
            raise ValueError("Message cannot be empty")

        request_started = time.perf_counter()

        # Step 1: create a trace for this request.
        trace = self.trace_service.start_trace(db)

        prompt = (
            "Bạn là Elec-Agent, trợ lý tham khảo về thiết bị "
            "điện gia dụng. Hãy trả lời bằng tiếng Việt, "
            "ngắn gọn và dễ hiểu. Không hướng dẫn người dùng "
            "thực hiện thao tác nguy hiểm với điện. Nếu có "
            "nguy cơ điện giật, cháy hoặc rò điện, hãy khuyên "
            "ngừng sử dụng và liên hệ thợ chuyên môn.\n\n"
            "Câu hỏi người dùng: "
            f"{question}"
        )

        model_name = "qwen2.5:3b"
        llm_started = time.perf_counter()

        # Step 2: call the LLM.
        try:
            with OllamaClient() as client:
                model_name = client.model
                answer = client.generate(prompt)

        except Exception as exc:
            llm_duration_ms = (
                time.perf_counter() - llm_started
            ) * 1000

            # Try to record the failed LLM step.
            try:
                self.trace_service.add_step(
                    db=db,
                    trace_id=trace.id,
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

                self.trace_service.fail_trace(
                    db=db,
                    trace=trace,
                    total_ms=total_ms,
                )

            except Exception:
                db.rollback()

            raise ChatServiceError(
                message="Cannot get a response from Ollama.",
                trace_id=str(trace.id),
                status_code=502,
            ) from exc

        llm_duration_ms = (
            time.perf_counter() - llm_started
        ) * 1000

        # Step 3: persist input, output, and latency.
        try:
            self.trace_service.add_step(
                db=db,
                trace_id=trace.id,
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

            self.trace_service.finish_trace(
                db=db,
                trace=trace,
                total_ms=total_ms,
            )

        except Exception as exc:
            db.rollback()

            raise ChatServiceError(
                message="LLM responded, but trace saving failed.",
                trace_id=str(trace.id),
                status_code=500,
            ) from exc

        # Step 4: return application-level result.
        return {
            "answer": answer.strip(),
            "trace_id": str(trace.id),
            "duration_ms": round(total_ms, 2),
        }