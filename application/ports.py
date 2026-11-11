from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Protocol

from domain.answer_review import ReviewDecision


class ChatGenerator(Protocol):
    @property
    def model_name(self) -> str: ...

    def generate(self, prompt: str) -> str: ...


@dataclass(frozen=True)
class RetrievedDocument:
    content: str
    source: str | None = None


class DocumentRetriever(Protocol):
    def retrieve(
        self,
        query: str,
        limit: int = 5,
    ) -> list[RetrievedDocument]: ...


class AnswerReviewer(Protocol):
    """P4-2: kiểm duyệt câu trả lời SAU khi sinh, trước khi trả cho người dùng.

    Là port riêng để ChatService không biết reviewer dùng luật hay cách khác;
    hiện thực mặc định là `domain.answer_review.RuleBasedAnswerReviewer`.
    """

    def review(self, question: str, answer: str) -> ReviewDecision: ...


class TraceRecorder(Protocol):
    def start_trace(self) -> uuid.UUID: ...

    def add_step(
        self,
        trace_id: uuid.UUID,
        step_order: int,
        step_name: str,
        input_data: Any = None,
        output_data: Any = None,
        duration_ms: float = 0.0,
    ) -> None: ...

    def finish_trace(
        self,
        trace_id: uuid.UUID,
        total_ms: float,
    ) -> None: ...

    def fail_trace(
        self,
        trace_id: uuid.UUID,
        total_ms: float,
    ) -> None: ...
