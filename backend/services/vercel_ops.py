"""Vercel layer — deploy a generated app from its workspace via the Vercel CLI.

Per ADR 0002: deploy directly from the workspace files (decoupled from GitHub). The
CLI uploads the source, Vercel builds it remotely, and prints the deployment URL, which
we parse out. Requires the `vercel` CLI installed and VERCEL_TOKEN in the environment.
"""

import os
import re
from pathlib import Path

from utils import shell

# Matches a Vercel deployment URL (single-label subdomain), e.g. https://my-app.vercel.app
_URL_RE = re.compile(r"https://[a-z0-9-]+\.vercel\.app")


def _token() -> str:
    token = os.getenv("VERCEL_TOKEN")
    if not token:
        raise ValueError("VERCEL_TOKEN is not set (add it to backend/.env)")
    return token


def _extract_url(output: str) -> str:
    """Pull the deployment URL out of the CLI output (the last vercel.app URL)."""
    matches = _URL_RE.findall(output)
    if not matches:
        raise RuntimeError(f"No deployment URL found in Vercel output:\n{output}")
    return matches[-1]


async def deploy(workspace_path: Path) -> str:
    """Deploy the workspace to Vercel (production) and return the live URL."""
    token = _token()
    result = await shell.run(
        ["vercel", "deploy", "--prod", "--yes", "--token", token],
        cwd=workspace_path,
        secret=token,
    )
    return _extract_url(result.stdout + "\n" + result.stderr)
