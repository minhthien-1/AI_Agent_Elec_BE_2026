from dataclasses import dataclass


@dataclass(frozen=True)
class ChatResult:
    answer: str
    trace_id: str
    duration_ms: float
