import pytest

from application.tools import ToolInputError, ToolResult
from infrastructure.tools.ask_clarification import AskClarificationTool


def test_ask_clarification_tool_declares_schema_and_builds_specific_questions():
    tool = AskClarificationTool()

    result = tool.run(
        {"missing_fields": ["device", "symptoms", "device"]}
    )

    assert tool.name == "ask_clarification"
    assert tool.description
    assert tool.parameters_schema["required"] == ["missing_fields"]
    assert result == ToolResult(
        content=(
            "Bạn đang gặp vấn đề với thiết bị nào? "
            "Thiết bị đang có biểu hiện cụ thể như thế nào?"
        )
    )


@pytest.mark.parametrize(
    ("arguments", "message"),
    (
        ({}, "'missing_fields'"),
        ({"missing_fields": []}, "'missing_fields'"),
        ({"missing_fields": "device"}, "'missing_fields'"),
        ({"missing_fields": [1]}, "only strings"),
        ({"missing_fields": ["unknown"]}, "Unsupported"),
        ({"missing_fields": ["device"], "extra": True}, "Unknown"),
    ),
)
def test_ask_clarification_tool_rejects_invalid_arguments(arguments, message):
    with pytest.raises(ToolInputError, match=message):
        AskClarificationTool().run(arguments)
