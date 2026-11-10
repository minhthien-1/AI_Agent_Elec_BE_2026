from fastapi import Depends
from sqlalchemy.orm import Session

from application.chat_service import ChatService
from infrastructure.llm.ollama_generator import OllamaGenerator
from infrastructure.persistence.database import get_db
from infrastructure.persistence.trace_service import TraceService
from infrastructure.rag.document_retriever import PgvectorDocumentRetriever


def get_chat_service(
    db: Session = Depends(get_db),
) -> ChatService:
    return ChatService(
        generator=OllamaGenerator(),
        trace_recorder=TraceService(db),
        document_retriever=PgvectorDocumentRetriever(db),
    )
