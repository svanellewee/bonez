from pathlib import Path


class WorkspaceError(ValueError):
    pass


class Workspace:
    def __init__(self, root: Path) -> None:
        self.root = root.expanduser().resolve()

        if not self.root.is_dir():
            raise WorkspaceError(
                f"Not a directory: {self.root}"
            )

    def resolve(self, relative_path: str) -> Path:
        path = (self.root / relative_path).resolve()

        try:
            path.relative_to(self.root)
        except ValueError as exc:
            raise WorkspaceError(
                "Path escapes workspace"
            ) from exc

        return path

    def list_files(self, limit: int = 200) -> list[str]:
        files: list[str] = []

        for path in sorted(self.root.rglob("*")):
            if any(
                part in {
                    ".git", ".venv", "__pycache__",
                    ".pytest_cache",
                }
                for part in path.parts
            ):
                continue

            if path.is_file():
                try:
                    path.resolve().relative_to(self.root)
                except ValueError:
                    continue

                files.append(
                    path.relative_to(self.root).as_posix()
                )

                if len(files) >= max(1, min(limit, 200)):
                    break

        return files

    def read_file(self, relative_path: str) -> str:
        path = self.resolve(relative_path)

        if not path.is_file():
            raise WorkspaceError(
                f"Not a file: {relative_path}"
            )

        content = path.read_text(encoding="utf-8")

        if len(content) > 20_000:
            content = content[:20_000] + "\n[truncated]"

        return content

    def write_file(
        self,
        relative_path: str,
        content: str,
    ) -> str:
        path = self.resolve(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

        return f"Wrote {relative_path}"
