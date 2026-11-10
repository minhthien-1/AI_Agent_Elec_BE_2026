from sqlalchemy.orm import Session

from application.ports import RetrievedDocument
from infrastructure.rag.retriever import PgvectorRetriever


class PgvectorDocumentRetriever:
    """Adapt the pgvector retriever to the application document port."""

    def __init__(
        self,
        db: Session,
        retriever: PgvectorRetriever | None = None,
    ) -> None:
        self.db = db
        self.retriever = retriever or PgvectorRetriever()

    def retrieve(
        self,
        query: str,
        limit: int = 5,
    ) -> list[RetrievedDocument]:
        chunks = self.retriever.retrieve(self.db, query, k=limit)
        return [
            RetrievedDocument(
                content=chunk.content,
                source=chunk.metadata.get("source"),
            )
            for chunk in chunks
        ]
