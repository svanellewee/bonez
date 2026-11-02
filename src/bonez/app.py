import os
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Input, Label, RichLog, Static

from bare_agent.agent import Agent
from bare_agent.client import OllamaClient
from bare_agent.tools import ToolExecutor
from bare_agent.workspace import Workspace


class ApprovalScreen(ModalScreen[bool]):
    BINDINGS = [("escape", "deny", "Deny")]

    def __init__(self, title: str, details: str) -> None:
        super().__init__()
        self.approval_title = title
        self.details = details

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self.approval_title)
            yield Static(self.details)
            with Horizontal():
                yield Button(
                    "Approve", variant="success", id="approve"
                )
                yield Button(
                    "Deny", variant="error", id="deny"
                )

    def on_button_pressed(
        self, event: Button.Pressed
    ) -> None:
        self.dismiss(event.button.id == "approve")

    def action_deny(self) -> None:
        self.dismiss(False)


class BareAgentApp(App[None]):
    TITLE = "Bare Agent"
    SUB_TITLE = "Ollama coding agent"

    CSS = """
    #transcript {
        height: 1fr;
        border: round $primary;
        margin: 0 1;
    }
    #status {
        height: 1;
        margin: 0 1;
    }
    #prompt-row {
        height: 3;
        margin: 0 1 1 1;
    }
    #prompt {
        width: 1fr;
    }
    #send {
        width: 12;
    }
    #dialog {
        width: 80%;
        max-width: 100;
        height: auto;
        max-height: 85%;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    #dialog Static {
        height: auto;
        max-height: 24;
        overflow-y: auto;
        border: round $secondary;
        padding: 1;
    }
    """

    def __init__(
        self,
        workspace: Path,
        model: str,
        ollama_host: str,
    ) -> None:
        super().__init__()
        self.workspace = Workspace(workspace)
        self.model = model
        self.client = OllamaClient(ollama_host)
        self.agent: Agent | None = None
        self.busy = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield RichLog(
            id="transcript",
            wrap=True,
            markup=False,
        )
        yield Label(
            f"{self.workspace.root} | {self.model}",
            id="status",
        )
        with Horizontal(id="prompt-row"):
            yield Input(
                placeholder="Describe a coding task…",
                id="prompt",
            )
            yield Button("Send", id="send")
        yield Footer()

    def on_mount(self) -> None:
        async def approve(
            title: str, details: str
        ) -> bool:
            return await self.push_screen_wait(
                ApprovalScreen(title, details)
            )

        self.agent = Agent(
            self.client,
            ToolExecutor(self.workspace, approve),
            self.model,
        )
        self.log(
            "system",
            "Ready. Writes and commands require approval.",
        )

    async def on_button_pressed(
        self, event: Button.Pressed
    ) -> None:
        if event.button.id == "send":
            await self.submit_prompt()

    async def on_input_submitted(
        self, event: Input.Submitted
    ) -> None:
        await self.submit_prompt()

    def log(self, kind: str, text: str) -> None:
        self.query_one("#transcript", RichLog).write(
            f"[{kind.upper()}]\n{text}\n"
        )

    async def submit_prompt(self) -> None:
        prompt_input = self.query_one("#prompt", Input)
        prompt = prompt_input.value.strip()

        if not prompt or self.busy or self.agent is None:
            return

        prompt_input.value = ""
        self.busy = True
        self.query_one("#send", Button).disabled = True
        self.log("you", prompt)

        async def emit(kind: str, text: str) -> None:
            if kind == "status":
                self.query_one("#status", Label).update(text)
            else:
                self.log(kind, text)

        try:
            await self.agent.ask(prompt, emit)
        except Exception as exc:
            self.log(
                "error",
                f"{type(exc).__name__}: {exc}",
            )
        finally:
            self.busy = False
            self.query_one("#send", Button).disabled = False
            prompt_input.focus()


def make_app(
    workspace: Path,
    model: str,
    ollama_host: str | None = None,
) -> BareAgentApp:
    return BareAgentApp(
        workspace,
        model,
        ollama_host or os.getenv(
            "OLLAMA_HOST",
            "http://127.0.0.1:11434",
        ),
    )
