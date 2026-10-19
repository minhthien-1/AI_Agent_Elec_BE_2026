from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from rag.embeddings import E5Embedder


@dataclass(frozen=True)
class RetrievedChunk:
    id: str
    content: str
    metadata: dict[str, Any]
    score: float


class PgvectorRetriever:
    def __init__(self, embedder: E5Embedder | None = None) -> None:
        self.embedder = embedder or E5Embedder()

    def retrieve(self, db: Session, query: str, k: int = 5) -> list[RetrievedChunk]:
        if not query or not query.strip():
            raise ValueError("query must not be empty")

        if k < 1:
            raise ValueError("k must be at least 1")

        query_vector = self.embedder.embed_query(query)

        statement = text("""
            SELECT
                id,
                content,
                metadata,
                1 - (embedding <=> CAST(:query_embedding AS vector)) AS score
            FROM chunks
            ORDER BY embedding <=> CAST(:query_embedding AS vector)
            LIMIT :k
        """)

        rows = db.execute(
            statement,
            {
                "query_embedding": str(query_vector),
                "k": k,
            },
        ).mappings()

        return [
            RetrievedChunk(
                id=str(row["id"]),
                content=row["content"],
                metadata=row["metadata"],
                score=float(row["score"]),
            )
            for row in rows
        ]