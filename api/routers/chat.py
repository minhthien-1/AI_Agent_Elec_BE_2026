from fastapi import APIRouter, Depends, HTTPException

from application.chat_service import (
    ChatApplicationError,
    ChatService,
)
from api.dependencies import get_chat_service
from api.schemas.chat import ChatRequest, ChatResponse


router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
):
    question = request.message.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty",
        )

    try:
        result = service.send_message(message=question)

    except ChatApplicationError as exc:
        status_code = (
            502
            if exc.kind in {"llm_failed", "retrieval_failed", "tool_failed"}
            else 500
        )
        raise HTTPException(
            status_code=status_code,
            detail={
                "message": exc.message,
                "trace_id": exc.trace_id,
            },
        ) from exc

    return ChatResponse(
        answer=result.answer,
        trace_id=result.trace_id,
        duration_ms=result.duration_ms,
    )