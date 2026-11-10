from typing import Any

from application.tools import ToolInputError, ToolResult


class AskClarificationTool:
    """Create a deterministic follow-up question for missing chat details."""

    name = "ask_clarification"
    description = (
        "Ask the user for missing appliance or symptom details before answering."
    )
    parameters_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "missing_fields": {
                "type": "array",
                "description": "Details that are needed to continue the consultation.",
                "items": {
                    "type": "string",
                    "enum": ["device", "symptoms", "brand", "model"],
                },
                "minItems": 1,
                "uniqueItems": True,
            },
        },
        "required": ["missing_fields"],
        "additionalProperties": False,
    }

    _QUESTIONS = {
        "device": "Bạn đang gặp vấn đề với thiết bị nào?",
        "symptoms": "Thiết bị đang có biểu hiện cụ thể như thế nào?",
        "brand": "Thiết bị của bạn thuộc hãng nào?",
        "model": "Bạn cho mình xin model hoặc mã sản phẩm trên tem thiết bị nhé?",
    }

    def run(self, arguments: dict[str, Any]) -> ToolResult:
        # Chỉ chấp nhận các trường đã công bố trong schema để câu hỏi luôn rõ ràng.
        unknown_arguments = set(arguments) - {"missing_fields"}
        if unknown_arguments:
            names = ", ".join(sorted(unknown_arguments))
            raise ToolInputError(
                f"Unknown ask_clarification argument(s): {names}"
            )

        missing_fields = arguments.get("missing_fields")
        if not isinstance(missing_fields, list) or not missing_fields:
            raise ToolInputError("'missing_fields' must be a non-empty list")
        if any(not isinstance(field, str) for field in missing_fields):
            raise ToolInputError("'missing_fields' must contain only strings")

        unique_fields = list(dict.fromkeys(missing_fields))
        unknown_fields = set(unique_fields) - self._QUESTIONS.keys()
        if unknown_fields:
            names = ", ".join(sorted(unknown_fields))
            raise ToolInputError(f"Unsupported missing field(s): {names}")

        questions = [self._QUESTIONS[field] for field in unique_fields]
        # Tránh tạo một câu hỏi quá dài nếu phía gọi đưa nhiều trường cùng lúc.
        content = " ".join(questions[:2])
        return ToolResult(content=content)
