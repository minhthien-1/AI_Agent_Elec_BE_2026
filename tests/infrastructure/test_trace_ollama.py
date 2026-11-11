import pytest

# Cần dịch vụ thật (PostgreSQL/Ollama) nên CI bỏ qua: pytest -m "not integration".
pytestmark = pytest.mark.integration

import time

from infrastructure.llm.ollama_client import OllamaClient
from infrastructure.persistence.database import SessionLocal
from infrastructure.persistence.models import Trace
from infrastructure.persistence.trace_service import TraceService


def test_ollama_with_trace():
    db = SessionLocal()
    trace_service = TraceService(db)

    trace = None

    try:
        trace_id = trace_service.start_trace()
        trace = db.get(Trace, trace_id)
        assert trace is not None

        prompt = (
            "Bạn là trợ lý tư vấn thiết bị điện gia dụng. "
            "Hãy trả lời ngắn gọn: "
            "Máy giặt không lên nguồn thì cần kiểm tra gì?"
        )

        start = time.perf_counter()

        with OllamaClient() as client:
            answer = client.generate(prompt)

        duration_ms = (
            time.perf_counter() - start
        ) * 1000

        trace_service.add_step(
            trace_id=trace.id,
            step_order=1,
            step_name="ollama",
            input_data={
                "model": "qwen2.5:3b",
                "prompt": prompt,
            },
            output_data={
                "text": answer,
            },
            duration_ms=duration_ms,
        )

        trace_service.finish_trace(
            trace_id=trace.id,
            total_ms=duration_ms,
        )

        assert answer.strip() != ""
        assert trace.status == "success"
        assert trace.total_ms is not None
        assert trace.total_ms > 0

    finally:
        if trace is not None:
            existing_trace = db.get(
                type(trace),
                trace.id,
            )

            if existing_trace is not None:
                db.delete(existing_trace)
                db.commit()

        db.close()