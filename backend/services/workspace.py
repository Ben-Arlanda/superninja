"""Filesystem layer for a Task's Generated App.

Each Task gets its own isolated directory under workspace/, seeded from the fixed
scaffold; the Agent's output overwrites app/page.tsx. Kept separate from the AI logic
in agents/ so file I/O and LLM calls don't tangle.
"""

import shutil
from pathlib import Path

from config import settings


def create_workspace(task_id: str) -> Path:
    """Copy the scaffold into workspace/{task_id}/ and return the path.

    Wipes any existing directory for this id first so re-runs start clean.
    """
    dest = settings.workspace_dir / task_id
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(settings.template_dir, dest)
    return dest


def write_page(workspace_path: Path, code: str) -> None:
    """Overwrite app/page.tsx in the given workspace with the generated code."""
    page_path = workspace_path / "app" / "page.tsx"
    page_path.write_text(code, encoding="utf-8")
