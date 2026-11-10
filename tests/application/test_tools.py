import pytest

from application.tools import (
    ToolInputError,
    ToolNotFoundError,
    ToolRegistry,
    ToolResult,
)
from infrastructure.tools.ask_clarification import AskClarificationTool


class EchoTool:
    name = "echo"
    description = "Return the supplied value."
    parameters_schema = {
        "type": "object",
        "properties": {"value": {"type": "string"}},
        "required": ["value"],
    }

    def run(self, arguments: dict) -> ToolResult:
        return ToolResult(content=arguments["value"])


def test_registry_executes_registered_tool_and_exposes_definition():
    registry = ToolRegistry([EchoTool()])

    result = registry.execute("echo", {"value": "hello"})

    assert result == ToolResult(content="hello")
    assert registry.definitions() == [
        {
            "name": "echo",
            "description": "Return the supplied value.",
            "parameters": EchoTool.parameters_schema,
        }
    ]


def test_registry_rejects_duplicate_tool_names():
    with pytest.raises(ValueError, match="Duplicate tool name: echo"):
        ToolRegistry([EchoTool(), EchoTool()])


def test_registry_reports_unknown_tool_and_non_object_arguments():
    registry = ToolRegistry([EchoTool()])

    with pytest.raises(ToolNotFoundError, match="missing"):
        registry.execute("missing", {})

    with pytest.raises(TypeError, match="dictionary"):
        registry.execute("echo", ["not", "an", "object"])


class InvalidMetadataTool(EchoTool):
    description = ""


def test_registry_rejects_incomplete_tool_metadata():
    with pytest.raises(ValueError, match="description"):
        ToolRegistry([InvalidMetadataTool()])


def test_registry_returns_a_copy_of_tool_schema():
    registry = ToolRegistry([EchoTool()])

    registry.definitions()[0]["parameters"]["properties"]["value"]["type"] = "integer"

    assert EchoTool.parameters_schema["properties"]["value"]["type"] == "string"


def test_registry_can_register_and_describe_both_initial_tools():
    registry = ToolRegistry([EchoTool(), AskClarificationTool()])

    definitions = registry.definitions()

    assert [definition["name"] for definition in definitions] == [
        "echo",
        "ask_clarification",
    ]
