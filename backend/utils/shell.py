"""Run external commands without blocking the async event loop.

`subprocess.run` is blocking; calling it directly inside an async task would freeze
the whole event loop (and all status polling) for the command's duration. We wrap it
in `asyncio.to_thread` so it runs on a worker thread and the loop stays responsive.
Reused by every shell-out step: git, npm, vercel.
"""

import asyncio
import subprocess
from pathlib import Path


class CommandError(RuntimeError):
    """Raised when an external command exits with a non-zero status."""


async def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run `cmd` (optionally in `cwd`) on a worker thread; raise on non-zero exit.

    Output is captured; on failure the CommandError message includes stderr so the
    Task can record a useful reason.
    """
    result = await asyncio.to_thread(
        subprocess.run, cmd, cwd=cwd, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise CommandError(
            f"`{' '.join(cmd)}` failed (exit {result.returncode}): {result.stderr.strip()}"
        )
    return result
