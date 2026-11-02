# tests/test_agent.py

from typing import Any

import pytest

from bonez.agent import Agent


class FakeOllamaClient:
    """Return predefined responses instead of calling Ollama."""

    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = responses
        self.calls: list[list[dict[str, Any]]] = []

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        self.calls.append(messages.copy())

        if not self.responses:
            raise AssertionError("Agent made an unexpected Ollama request")

        return self.responses.pop(0)


class FakeToolExecutor:
    """Record tool calls and return predictable results."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def execute(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> str:
        self.calls.append((name, arguments))
        return "file1.py\nfile2.py"


@pytest.mark.asyncio
async def test_agent_returns_final_answer() -> None:
    client = FakeOllamaClient(
        responses=[
            {
                "message": {
                    "role": "assistant",
                    "content": "The project contains two Python files.",
                }
            }
        ]
    )
    tools = FakeToolExecutor()
    agent = Agent(client=client, tools=tools)

    result = await agent.run("List the project files")

    assert result == "The project contains two Python files."
    assert len(client.calls) == 1
    assert tools.calls == []


@pytest.mark.asyncio
async def test_agent_executes_tool_then_returns_answer() -> None:
    client = FakeOllamaClient(
        responses=[
            {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "list_files",
                                "arguments": {},
                            }
                        }
                    ],
                }
            },
            {
                "message": {
                    "role": "assistant",
                    "content": "I found file1.py and file2.py.",
                }
            },
        ]
    )
    tools = FakeToolExecutor()
    agent = Agent(client=client, tools=tools)

    result = await agent.run("List the project files")

    assert result == "I found file1.py and file2.py."
    assert tools.calls == [("list_files", {})]
    assert len(client.calls) == 2


@pytest.mark.asyncio
async def test_agent_stops_at_step_limit() -> None:
    client = FakeOllamaClient(
        responses=[
            {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "list_files",
                                "arguments": {},
                            }
                        }
                    ],
                }
            },
            {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "list_files",
                                "arguments": {},
                            }
                        }
                    ],
                }
            },
        ]
    )
    tools = FakeToolExecutor()
    agent = Agent(client=client, tools=tools, max_steps=2)

    result = await agent.run("Keep listing files")

    assert len(client.calls) == 2
    assert len(tools.calls) == 2
    assert "limit" in result.lower()
