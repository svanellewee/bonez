import pytest

from bare_agent.tools import ToolExecutor
from bare_agent.workspace import Workspace


@pytest.mark.asyncio
async def test_write_requires_approval(tmp_path):
    async def deny(title, details):
        return False

    executor = ToolExecutor(Workspace(tmp_path), deny)

    result = await executor.execute(
        "write_file",
        {"path": "main.py", "content": "print('no')"},
    )

    assert "Denied" in result
    assert not (tmp_path / "main.py").exists()


@pytest.mark.asyncio
async def test_approved_write(tmp_path):
    async def approve(title, details):
        return True

    executor = ToolExecutor(Workspace(tmp_path), approve)

    result = await executor.execute(
        "write_file",
        {"path": "main.py", "content": "print('yes')"},
    )

    assert "Wrote" in result
    assert (tmp_path / "main.py").read_text() == "print('yes')"


@pytest.mark.asyncio
async def test_command_requires_approval(tmp_path):
    async def deny(title, details):
        return False

    executor = ToolExecutor(Workspace(tmp_path), deny)

    result = await executor.execute(
        "run_command",
        {"argv": ["python", "-c", "print('no')"]},
    )

    assert "Denied" in result
