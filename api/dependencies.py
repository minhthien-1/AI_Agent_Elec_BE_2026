from fastapi import Depends
from sqlalchemy.orm import Session

from application.chat_service import ChatService
from application.tools import ToolRegistry
from domain.answer_review import RuleBasedAnswerReviewer
from infrastructure.llm.ollama_generator import OllamaGenerator
from infrastructure.persistence.database import get_db
from infrastructure.persistence.trace_service import TraceService
from infrastructure.rag.document_retriever import PgvectorDocumentRetriever
from infrastructure.tools.ask_clarification import AskClarificationTool
from infrastructure.tools.search_manual import SearchManualTool


def get_chat_service(
    db: Session = Depends(get_db),
) -> ChatService:
    # Đăng ký adapter ở API để application không phụ thuộc hạ tầng cụ thể.
    document_retriever = PgvectorDocumentRetriever(db)
    return ChatService(
        generator=OllamaGenerator(),
        trace_recorder=TraceService(db),
        tools=ToolRegistry(
            [
                SearchManualTool(document_retriever),
                AskClarificationTool(),
            ]
        ),
        # P4-2: reviewer dùng luật, không gọi Ollama; có thể thay hiện thực khác qua port.
        reviewer=RuleBasedAnswerReviewer(),
    )
