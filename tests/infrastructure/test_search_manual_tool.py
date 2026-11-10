import pytest

from application.ports import RetrievedDocument
from application.tools import ToolInputError, ToolResult
from infrastructure.tools.search_manual import SearchManualTool


class FakeDocumentRetriever:
    def __init__(self, documents: list[RetrievedDocument]):
        self.documents = documents
        self.query = None
        self.limit = None

    def retrieve(self, query: str, limit: int = 5) -> list[RetrievedDocument]:
        self.query = query
        self.limit = limit
        return self.documents[:limit]


def test_search_manual_tool_has_metadata_and_returns_formatted_sources():
    retriever = FakeDocumentRetriever(
        [
            RetrievedDocument(
                content="Kiểm tra phích cắm theo hướng dẫn.",
                source="washer_manual.pdf",
            )
        ]
    )
    tool = SearchManualTool(retriever)

    result = tool.run({"query": "  máy giặt không lên nguồn ", "limit": 2})

    assert tool.name == "search_manual"
    assert tool.description
    assert tool.parameters_schema["required"] == ["query"]
    assert result == ToolResult(
        content="[1] Source: washer_manual.pdf\n"
        "Kiểm tra phích cắm theo hướng dẫn."
    )
    assert retriever.query == "máy giặt không lên nguồn"
    assert retriever.limit == 2


@pytest.mark.parametrize(
    ("arguments", "error"),
    (
        ({}, "'query'"),
        ({"query": ""}, "'query'"),
        ({"query": "máy giặt", "limit": True}, "'limit'"),
        ({"query": "máy giặt", "limit": 0}, "between 1 and 5"),
        ({"query": "máy giặt", "extra": "no"}, "Unknown"),
    ),
)
def test_search_manual_tool_rejects_invalid_arguments(arguments, error):
    tool = SearchManualTool(FakeDocumentRetriever([]))

    with pytest.raises(ToolInputError, match=error):
        tool.run(arguments)


def test_search_manual_tool_returns_empty_content_when_no_document_found():
    tool = SearchManualTool(FakeDocumentRetriever([]))

    result = tool.run({"query": "không có tài liệu"})

    assert result.content == ""
