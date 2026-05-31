"""Local Git operations for a generated app's workspace.

Per ADR 0002, each Task's Generated App becomes its own repo. Phase 3 does the local
half: initialise a fresh repo on `main` and commit everything. The push (Phase 4) is
separate. Commits are authored by a fixed bot identity via per-command `-c` flags, so
we never touch the machine's global git config.
"""

from pathlib import Path

from utils.shell import run

_BOT_NAME = "SuperNinja Bot"
_BOT_EMAIL = "bot@superninja.local"


async def init_and_commit(workspace_path: Path, prompt: str) -> None:
    """Init a fresh git repo in the workspace and commit all files on branch `main`."""
    await run(["git", "init", "-b", "main"], cwd=workspace_path)
    await run(["git", "add", "-A"], cwd=workspace_path)
    message = f"Initial commit — SuperNinja generated app\n\nPrompt: {prompt}"
    await run(
        [
            "git",
            "-c",
            f"user.name={_BOT_NAME}",
            "-c",
            f"user.email={_BOT_EMAIL}",
            "commit",
            "-m",
            message,
        ],
        cwd=workspace_path,
    )
