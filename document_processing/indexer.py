"""Chunk source documents, embed them locally, and upsert them into pgvector."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Optional, Sequence

from sqlalchemy.dialects.postgresql import insert

from db.database import SessionLocal
from db.models import Chunk
from document_processing.chunker import chunk_document
from document_processing.cleaner import clean_document
from document_processing.reader import READERS, read_document
from rag.embeddings import E5Embedder


def _source_files(input_path: Path) -> Iterable[Path]:
    if input_path.is_file():
        if input_path.suffix.lower() not in READERS:
            raise ValueError(f"Unsupported file type: {input_path.suffix}")
        yield input_path
        return
    if not input_path.is_dir():
        raise FileNotFoundError(f"Input not found: {input_path}")
    yield from (
        path for path in sorted(input_path.rglob("*"))
        if path.is_file() and path.suffix.lower() in READERS
    )


def index_documents(input_value: str, batch_size: int = 32) -> dict[str, int]:
    input_path = Path(input_value).expanduser()
    chunks = []
    files = 0
    for path in _source_files(input_path):
        document = clean_document(read_document(path))
        files += 1
        for chunk in chunk_document(document):
            chunks.append((path, document, chunk))

    embedder = E5Embedder()
    db = SessionLocal()
    try:
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            vectors = embedder.embed_passages((item[2].text for item in batch), batch_size)
            rows = []
            for (path, document, chunk), vector in zip(batch, vectors):
                metadata = {
                    **chunk.metadata, "source_path": str(path),
                    "filename": document.filename, "file_type": document.file_type,
                    "token_count": chunk.token_count,
                }
                rows.append({"chunk_key": chunk.chunk_id, "content": chunk.text,
                             "embedding": vector, "metadata": metadata})
            if rows:
                # Use the table rather than the ORM class: SQLAlchemy reserves
                # ``metadata`` on declarative models, while the database column
                # is intentionally named ``metadata``.
                statement = insert(Chunk.__table__).values(rows)
                statement = statement.on_conflict_do_update(
                    index_elements=[Chunk.__table__.c.chunk_key],
                    set_={"content": statement.excluded.content,
                          "embedding": statement.excluded.embedding,
                          "metadata": statement.excluded["metadata"]},
                )
                db.execute(statement)
                db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return {"files": files, "chunks": len(chunks)}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Index documents into pgvector.")
    parser.add_argument("--input", required=True, help="Source file or directory")
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args(argv)
    if args.batch_size <= 0:
        parser.error("--batch-size must be greater than zero")
    print(json.dumps(index_documents(args.input, args.batch_size), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
