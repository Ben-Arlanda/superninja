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


async def run(
    cmd: list[str], cwd: Path | None = None, secret: str | None = None
) -> subprocess.CompletedProcess:
    """Run `cmd` (optionally in `cwd`) on a worker thread; raise on non-zero exit.

    On failure the CommandError reports only the program name (not the args, which may
    contain a token/URL) plus stderr — and any `secret` passed is redacted from stderr.
    """
    result = await asyncio.to_thread(
        subprocess.run, cmd, cwd=cwd, capture_output=True, text=True
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        if secret:
            stderr = stderr.replace(secret, "***")
        raise CommandError(f"`{cmd[0]}` failed (exit {result.returncode}): {stderr}")
    return result
