"""Ingest supported documents into the pgvector knowledge base.

Run from the repository root, for example:

    python -m app.rag.ingest data/manuals
"""

from __future__ import annotations

import argparse
import json
import time
from typing import Optional, Sequence

from document_processing.indexer import index_documents


def ingest(input_path: str, batch_size: int = 32) -> dict[str, int | float]:
    """Index documents and return the source/chunk counts plus elapsed seconds."""
    started_at = time.perf_counter()
    summary = index_documents(input_path, batch_size=batch_size)
    return {
        "files": summary["files"],
        "chunks": summary["chunks"],
        "duration_seconds": round(time.perf_counter() - started_at, 2),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read, chunk, embed, and upsert documents into pgvector."
    )
    parser.add_argument(
        "input_path",
        help="A supported source file or a directory to scan recursively.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Number of chunks encoded and upserted per batch (default: 32).",
    )
    args = parser.parse_args(argv)
    if args.batch_size <= 0:
        parser.error("--batch-size must be greater than zero")

    print(json.dumps(ingest(args.input_path, args.batch_size), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
