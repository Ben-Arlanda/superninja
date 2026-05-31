"""Git ops + shell helper tests. Uses real git in a temp dir (fast, deterministic)."""

import asyncio

import pytest

from services import git_ops
from utils.shell import CommandError, run


def test_init_and_commit_creates_main_branch_with_bot_author(tmp_path):
    (tmp_path / "file.txt").write_text("hello")

    asyncio.run(git_ops.init_and_commit(tmp_path, "a boxing gym"))

    branch = asyncio.run(
        run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=tmp_path)
    ).stdout.strip()
    assert branch == "main"

    author = asyncio.run(
        run(["git", "log", "-1", "--format=%an <%ae>"], cwd=tmp_path)
    ).stdout.strip()
    assert author == "SuperNinja Bot <bot@superninja.local>"

    tracked = asyncio.run(run(["git", "ls-files"], cwd=tmp_path)).stdout
    assert "file.txt" in tracked


def test_shell_run_raises_commanderror_on_nonzero(tmp_path):
    # `git status` in a non-repo directory exits non-zero.
    with pytest.raises(CommandError):
        asyncio.run(run(["git", "status"], cwd=tmp_path))
