import pytest

from bonez.workspace import Workspace, WorkspaceError


def test_list_and_read(tmp_path):
    (tmp_path / "main.py").write_text("print('hello')")
    workspace = Workspace(tmp_path)

    assert workspace.list_files() == ["main.py"]
    assert workspace.read_file("main.py") == "print('hello')"


def test_write_file(tmp_path):
    workspace = Workspace(tmp_path)
    workspace.write_file("src/main.py", "print('ok')")

    assert (tmp_path / "src/main.py").read_text() == "print('ok')"


def test_reject_path_traversal(tmp_path):
    workspace = Workspace(tmp_path)

    with pytest.raises(WorkspaceError):
        workspace.resolve("../outside.txt")
