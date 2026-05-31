"""GitHub layer — create a fresh public repo per Task and push its workspace.

Per ADR 0002: a fresh repo per Task on the personal account; the push is archival.
Repos are created via the GitHub REST API (httpx) using the classic PAT in
GITHUB_TOKEN. The token is handed to git only inside the one-off push command, so it
never gets written to the workspace's .git/config.
"""

import os
import re
from pathlib import Path

import httpx

from utils import shell

GITHUB_API = "https://api.github.com"


def _slugify(text: str, max_len: int = 40) -> str:
    """Lowercase, punctuation -> hyphens, trimmed and truncated. GitHub-name safe."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len].strip("-") or "app"


def _token() -> str:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN is not set (add it to backend/.env)")
    return token


async def _create_repo(name: str, *, private: bool = False) -> dict:
    """Create a repo via the GitHub API; return its JSON (clone_url, html_url, ...)."""
    headers = {
        "Authorization": f"Bearer {_token()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    body = {"name": name, "private": private, "auto_init": False}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{GITHUB_API}/user/repos", headers=headers, json=body)
    if resp.status_code >= 300:
        raise RuntimeError(f"GitHub repo creation failed ({resp.status_code}): {resp.text}")
    return resp.json()


async def create_and_push(workspace_path: Path, prompt: str, task_id: str) -> str:
    """Create a fresh public repo and push the workspace to it. Returns the repo URL."""
    name = f"{_slugify(prompt)}-{task_id[:8]}"
    repo = await _create_repo(name, private=False)
    clone_url = repo["clone_url"]  # https://github.com/<owner>/<name>.git
    html_url = repo["html_url"]

    # Clean remote saved on disk; token lives only in the transient push URL.
    token = _token()
    push_url = clone_url.replace("https://", f"https://x-access-token:{token}@", 1)
    await shell.run(["git", "remote", "add", "origin", clone_url], cwd=workspace_path)
    await shell.run(["git", "push", push_url, "main"], cwd=workspace_path, secret=token)
    return html_url
