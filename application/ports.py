from __future__ import annotations

import uuid
from typing import Any, Protocol


class ChatGenerator(Protocol):
    @property
    def model_name(self) -> str: ...

    def generate(self, prompt: str) -> str: ...


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
