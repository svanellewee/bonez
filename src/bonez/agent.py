import json
from collections.abc import Awaitable, Callable
from typing import Any

from bonez.client import OllamaClient
from bonez.tools import ToolExecutor, tool_definitions

Emit = Callable[[str, str], Awaitable[None]]


class Agent:
    def __init__(
        self,
        client: OllamaClient,
        executor: ToolExecutor,
        model: str,
        max_steps: int = 8,
    ) -> None:
        self.client = client
        self.executor = executor
        self.model = model
        self.max_steps = max_steps

        self.messages: list[dict[str, Any]] = [{
            "role": "system",
            "content": (
                "You are a coding assistant. Inspect the "
                "workspace before changing code. Use tools "
                "when useful. Never claim an operation "
                "succeeded unless its result confirms it. "
                "Respect approval denials. Make small changes "
                "and run relevant tests when approved."
            ),
        }]

    async def ask(
        self,
        prompt: str,
        emit: Emit,
    ) -> str:
        self.messages.append({
            "role": "user",
            "content": prompt,
        })

        for step in range(self.max_steps):
            await emit(
                "status",
                f"Thinking: step {step + 1}/{self.max_steps}",
            )

            message = await self.client.chat(
                model=self.model,
                messages=self.messages,
                tools=tool_definitions(),
            )

            self.messages.append(message)
            tool_calls = message.get("tool_calls", [])

            if not tool_calls:
                answer = str(
                    message.get("content")
                    or "(Empty model response)"
                )
                await emit("assistant", answer)
                return answer

            for call in tool_calls:
                function = call.get("function", {})
                name = str(function.get("name", ""))
                args = function.get("arguments", {})

                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}

                if not isinstance(args, dict):
                    args = {}

                await emit(
                    "tool",
                    f"{name}: {json.dumps(args)}",
                )

                result = await self.executor.execute(
                    name, args
                )

                await emit("result", result[:3000])

                self.messages.append({
                    "role": "tool",
                    "tool_name": name,
                    "content": result,
                })

        answer = (
            f"Stopped after {self.max_steps} model steps."
        )
        await emit("assistant", answer)
        return answer
