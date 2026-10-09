from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from agent.chat_service import (
    ChatService,
    ChatServiceError,
)
from api.schemas.chat import ChatRequest, ChatResponse
from db.database import get_db


router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    question = request.message.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty",
        )

    service = ChatService()

    try:
        result = service.send_message(
            db=db,
            message=question,
        )

    except ChatServiceError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "message": exc.message,
                "trace_id": exc.trace_id,
            },
        ) from exc

    return ChatResponse(**result)