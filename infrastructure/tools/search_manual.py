from typing import Any

from application.ports import DocumentRetriever
from application.tools import ToolInputError, ToolResult


class SearchManualTool:
    """Search indexed appliance documents through the common agent-tool contract."""

    name = "search_manual"
    description = (
        "Search appliance manuals and technical documents for an answer "
        "to a device question."
    )
    parameters_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Question or terms to search in appliance documents.",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of passages to return (1-5).",
                "minimum": 1,
                "maximum": 5,
                "default": 5,
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    }

    def __init__(self, retriever: DocumentRetriever) -> None:
        self.retriever = retriever

    def run(self, arguments: dict[str, Any]) -> ToolResult:
        # Kiểm tra đầu vào trước khi chuyển truy vấn xuống tầng RAG.
        unknown_arguments = set(arguments) - {"query", "limit"}
        if unknown_arguments:
            names = ", ".join(sorted(unknown_arguments))
            raise ToolInputError(f"Unknown search_manual argument(s): {names}")

        query = arguments.get("query")
        if not isinstance(query, str) or not query.strip():
            raise ToolInputError("'query' must be a non-empty string")

        limit = arguments.get("limit", 5)
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise ToolInputError("'limit' must be an integer")
        if not 1 <= limit <= 5:
            raise ToolInputError("'limit' must be between 1 and 5")

        documents = self.retriever.retrieve(query.strip(), limit=limit)
        content = "\n\n".join(
            f"[{index}] Source: {document.source or 'unknown'}\n"
            f"{document.content}"
            for index, document in enumerate(documents, start=1)
        )
        return ToolResult(content=content)
