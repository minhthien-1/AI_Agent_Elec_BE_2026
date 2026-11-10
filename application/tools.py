from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Protocol, Sequence


# Chuẩn hóa kết quả để bên gọi không phụ thuộc kiểu dữ liệu riêng của từng tool.
@dataclass(frozen=True)
class ToolResult:
    """Standard result returned by every tool."""

    content: str


class AgentTool(Protocol):
    """Common name, description, JSON parameters, and run contract for agent tools."""

    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    @property
    def parameters_schema(self) -> dict[str, Any]: ...

    def run(self, arguments: dict[str, Any]) -> ToolResult: ...


class ToolError(Exception):
    """Base error for tool registration and execution failures."""


class ToolNotFoundError(ToolError):
    """Raised when a caller requests a tool that was not registered."""


class ToolInputError(ToolError, ValueError):
    """Raised when tool arguments do not satisfy the tool's input contract."""


class ToolRegistry:
    """Central registry that gives every tool the same registration and call path."""

    def __init__(self, tools: Sequence[AgentTool]) -> None:
        self._tools: dict[str, AgentTool] = {}
        for tool in tools:
            if not tool.name.strip():
                raise ValueError("Tool name cannot be empty")
            if not tool.description.strip():
                raise ValueError(f"Tool description cannot be empty: {tool.name}")
            if not isinstance(tool.parameters_schema, dict):
                raise TypeError(
                    f"Tool parameters_schema must be a dict: {tool.name}"
                )
            if tool.name in self._tools:
                raise ValueError(f"Duplicate tool name: {tool.name}")
            self._tools[tool.name] = tool

    def execute(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> ToolResult:
        # Registry kiểm tra cách gọi chung; từng tool kiểm tra tham số theo schema riêng.
        tool = self._tools.get(name)
        if tool is None:
            raise ToolNotFoundError(f"Tool is not registered: {name}")
        if not isinstance(arguments, dict):
            raise TypeError("Tool arguments must be a dictionary")
        return tool.run(arguments)

    def definitions(self) -> list[dict[str, Any]]:
        """Expose metadata for tests, diagnostics, and a future LLM tool-call adapter."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": deepcopy(tool.parameters_schema),
            }
            for tool in self._tools.values()
        ]
