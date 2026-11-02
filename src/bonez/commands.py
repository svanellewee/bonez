import asyncio
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


async def run_command(
    argv: list[str],
    cwd: Path,
    timeout_seconds: float = 30.0,
) -> CommandResult:
    if not argv or not all(
        isinstance(arg, str) for arg in argv
    ):
        raise ValueError(
            "argv must be a non-empty list of strings"
        )

    process = await asyncio.create_subprocess_exec(
        *argv,
        cwd=str(cwd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout_seconds,
        )
    except asyncio.TimeoutError:
        process.kill()
        stdout, stderr = await process.communicate()

        return CommandResult(
            returncode=-1,
            stdout=stdout.decode(errors="replace"),
            stderr=stderr.decode(errors="replace"),
            timed_out=True,
        )

    return CommandResult(
        returncode=process.returncode or 0,
        stdout=stdout.decode(errors="replace"),
        stderr=stderr.decode(errors="replace"),
    )
