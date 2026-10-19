from unittest.mock import MagicMock

import pytest

from app.rag.retriever import PgvectorRetriever


def make_db_with_rows(rows: list[dict]) -> MagicMock:
    """Tạo DB giả, không cần PostgreSQL thật cho unit test."""
    db = MagicMock()
    result = MagicMock()
    result.mappings.return_value = rows
    db.execute.return_value = result
    return db


def test_retrieve_embeds_query_executes_cosine_sql_and_returns_chunks() -> None:
    embedder = MagicMock()
    embedder.embed_query.return_value = [0.1, 0.2, 0.3]

    db = make_db_with_rows(
        [
            {
                "id": "chunk-1",
                "content": "Kiểm tra dây nguồn và ổ cắm.",
                "metadata": {"source": "manual.pdf", "page": 2},
                "score": 0.95,
            },
            {
                "id": "chunk-2",
                "content": "Kiểm tra cầu chì của máy giặt.",
                "metadata": {"source": "manual.pdf", "page": 3},
                "score": 0.82,
            },
        ]
    )

    results = PgvectorRetriever(embedder).retrieve(
        db,
        "Máy giặt không lên nguồn",
        k=2,
    )

    # Query phải dùng embedding query của E5.
    embedder.embed_query.assert_called_once_with("Máy giặt không lên nguồn")

    # Kiểm tra câu SQL và tham số truyền vào.
    db.execute.assert_called_once()
    statement, params = db.execute.call_args.args

    assert "embedding <=>" in statement.text
    assert "ORDER BY embedding <=>" in statement.text
    assert "LIMIT :k" in statement.text
    assert params == {
        "query_embedding": "[0.1, 0.2, 0.3]",
        "k": 2,
    }

    # Kiểm tra dữ liệu trả về.
    assert len(results) == 2

    assert results[0].id == "chunk-1"
    assert results[0].content == "Kiểm tra dây nguồn và ổ cắm."
    assert results[0].metadata == {"source": "manual.pdf", "page": 2}
    assert results[0].score == 0.95

    assert results[1].id == "chunk-2"
    assert results[1].score == 0.82


@pytest.mark.parametrize(
    ("query", "k", "error_message"),
    [
        ("", 5, "query must not be empty"),
        ("   ", 5, "query must not be empty"),
        ("máy giặt không lên nguồn", 0, "k must be at least 1"),
        ("máy giặt không lên nguồn", -1, "k must be at least 1"),
    ],
)
def test_retrieve_rejects_invalid_input(
    query: str,
    k: int,
    error_message: str,
) -> None:
    embedder = MagicMock()
    db = MagicMock()

    with pytest.raises(ValueError, match=error_message):
        PgvectorRetriever(embedder).retrieve(db, query, k=k)

    # Input không hợp lệ thì không được gọi embedding hay database.
    embedder.embed_query.assert_not_called()
    db.execute.assert_not_called()


def test_retrieve_returns_empty_list_when_database_has_no_chunks() -> None:
    embedder = MagicMock()
    embedder.embed_query.return_value = [0.1, 0.2, 0.3]

    db = make_db_with_rows([])

    results = PgvectorRetriever(embedder).retrieve(
        db,
        "Tủ lạnh không lạnh",
        k=3,
    )

    assert results == []