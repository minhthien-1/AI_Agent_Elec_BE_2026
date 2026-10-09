from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
    )


class ChatResponse(BaseModel):
    answer: str
    trace_id: str
    duration_ms: float