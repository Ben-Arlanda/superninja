"""The task runner — drives a Task through its lifecycle in the background.

Phase 2: the `generating_files` step is now REAL (the Agent generates the app into
its workspace). The commit/push/deploy steps remain stubs until Phases 4-6. The
surrounding structure (statuses, logging, failure handling) is unchanged.
"""

import asyncio

from agents.page_generator import generate_page_code
from models.task import Task, TaskStatus
from services import workspace

STEP_DELAY_SECONDS = 0.5


async def run_task(task: Task) -> None:
    """Drive a Task from pending to completed (or failed)."""
    try:
        task.status = TaskStatus.running
        task.log("Task started.")

        # --- REAL (Phase 2): generate the app into its own workspace ---
        task.status = TaskStatus.generating_files
        task.log("Creating workspace from scaffold...")
        workspace_path = workspace.create_workspace(task.id)
        task.log("Generating landing page with Claude (Opus 4.8)...")
        code = await generate_page_code(task.prompt)
        workspace.write_page(workspace_path, code)
        task.log(f"Generated app/page.tsx ({len(code)} characters).")

        # --- STUBS (become real in Phases 4-6) ---
        task.status = TaskStatus.committing
        task.log("Committing generated code to Git... (stub)")
        await asyncio.sleep(STEP_DELAY_SECONDS)

        task.status = TaskStatus.pushing
        task.log("Pushing code to GitHub... (stub)")
        await asyncio.sleep(STEP_DELAY_SECONDS)

        task.status = TaskStatus.deploying
        task.log("Deploying to Vercel... (stub)")
        await asyncio.sleep(STEP_DELAY_SECONDS)

        task.deployment_url = f"https://superninja-demo-{task.id[:8]}.vercel.app"
        task.status = TaskStatus.completed
        task.log(f"Deployment complete: {task.deployment_url}")
    except Exception as exc:  # noqa: BLE001 - any failure must land on the task
        task.status = TaskStatus.failed
        task.error = str(exc)
        task.log(f"Task failed: {exc}")
