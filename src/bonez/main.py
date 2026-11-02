import argparse
import os
from pathlib import Path

from bare_agent.app import make_app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
    )
    parser.add_argument(
        "--model",
        default=os.getenv(
            "BARE_AGENT_MODEL", "qwen3.5:4b"
        ),
    )
    parser.add_argument(
        "--ollama-host",
        default=os.getenv(
            "OLLAMA_HOST",
            "http://127.0.0.1:11434",
        ),
    )
    args = parser.parse_args()

    workspace = args.workspace.expanduser().resolve()

    if not workspace.is_dir():
        parser.error(f"Not a directory: {workspace}")

    make_app(
        workspace,
        args.model,
        args.ollama_host,
    ).run()


if __name__ == "__main__":
    main()
