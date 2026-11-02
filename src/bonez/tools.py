import json
from collections.abc import Awaitable, Callable
from typing import Any

from bare_agent.commands import run_command
from bare_agent.workspace import Workspace

Approval = Callable[[str, str], Awaitable[bool]]


def tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "List files in the workspace",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer"}
                    },
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a workspace text file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"}
                    },
                    "required": ["path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Write a file; requires approval",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["path", "content"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_command",
                "description": (
                    "Run a command as an argv list; "
                    "requires approval"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "argv": {
                            "type": "array",
                            "items": {"type": "string"},
                        }
                    },
                    "required": ["argv"],
                },
            },
        },
    ]


class ToolExecutor:
    def __init__(
        self,
        workspace: Workspace,
        approve: Approval,
    ) -> None:
        self.workspace = workspace
        self.approve = approve

    async def execute(
        self,
        name: str,
        args: dict[str, Any],
    ) -> str:
        try:
            if name == "list_files":
                return json.dumps(
                    self.workspace.list_files(
                        int(args.get("limit", 200))
                    )
                )

            if name == "read_file":
                return self.workspace.read_file(
                    str(args["path"])
                )

            if name == "write_file":
                path = str(args["path"])
                content = str(args["content"])

                approved = await self.approve(
                    "Approve file write",
                    f"Path: {path}\n\n{content[:5000]}",
                )

                if not approved:
                    return "Denied by user; file unchanged."

                return self.workspace.write_file(
                    path, content
                )

            if name == "run_command":
                argv = args["argv"]

                if (
                    not isinstance(argv, list)
                    or not argv
                    or not all(
                        isinstance(item, str)
                        for item in argv
                    )
                ):
                    return "Error: invalid argv"

                approved = await self.approve(
                    "Approve command",
                    json.dumps(argv),
                )

                if not approved:
                    return "Denied by user; command not run."

                result = await run_command(
                    argv, self.workspace.root
                )

                return json.dumps({
                    "returncode": result.returncode,
                    "stdout": result.stdout[-12000:],
                    "stderr": result.stderr[-12000:],
                    "timed_out": result.timed_out,
                })

            return f"Unknown tool: {name}"

        except (
            KeyError, TypeError, ValueError, OSError
        ) as exc:
            return f"Tool error: {type(exc).__name__}: {exc}"
