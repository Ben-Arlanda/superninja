"""The stub Agent — a tracer bullet that exercises the full task lifecycle.

Phase 1 has no real generation/Git/Vercel yet. This fake executor walks a Task
through every real status with short delays and log lines, then sets a fake
deployment URL. Later phases replace each step's body with real work; the
surrounding machinery (statuses, logging, failure handling) stays the same.
"""

import asyncio

from models.task import Task, TaskStatus

# Each tuple is (status to set, log message) for one step of the fake pipeline.
# Order matters — this is the lifecycle the UI will watch advance.
_STEPS: list[tuple[TaskStatus, str]] = [
    (TaskStatus.running, "Task started."),
    (TaskStatus.generating_files, "Generating application files..."),
    (TaskStatus.committing, "Committing generated code to Git..."),
    (TaskStatus.pushing, "Pushing code to GitHub..."),
    (TaskStatus.deploying, "Deploying to Vercel..."),
]

STEP_DELAY_SECONDS = 0.5


async def run_task(task: Task) -> None:
    """Drive a Task from pending to completed (or failed) in the background."""
    try:
        for status, message in _STEPS:
            task.status = status
            task.log(message)
            await asyncio.sleep(STEP_DELAY_SECONDS)

        task.deployment_url = f"https://superninja-demo-{task.id[:8]}.vercel.app"
        task.status = TaskStatus.completed
        task.log(f"Deployment complete: {task.deployment_url}")
    except Exception as exc:  # noqa: BLE001 - any failure must land on the task, not crash silently
        task.status = TaskStatus.failed
        task.error = str(exc)
        task.log(f"Task failed: {exc}")
