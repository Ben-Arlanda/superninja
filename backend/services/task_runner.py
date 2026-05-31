"""The task runner — drives a Task through its full lifecycle in the background.

The pipeline is now fully real: generate (Agent) → commit (git) → push (GitHub) →
deploy (Vercel). The try/except keeps a failed step from crashing silently — it lands
on the Task as `failed` + an error message.
"""

from agents.page_generator import generate_page_code
from models.task import Task, TaskStatus
from services import git_ops, github_ops, vercel_ops, workspace


async def run_task(task: Task) -> None:
    """Drive a Task from pending to completed (or failed)."""
    try:
        task.status = TaskStatus.running
        task.log("Task started.")

        # Generate the app into its own workspace
        task.status = TaskStatus.generating_files
        task.log("Creating workspace from scaffold...")
        workspace_path = workspace.create_workspace(task.id)
        task.log("Generating landing page with Claude (Opus 4.8)...")
        code = await generate_page_code(task.prompt)
        workspace.write_page(workspace_path, code)
        task.log(f"Generated app/page.tsx ({len(code)} characters).")

        # Commit to a fresh local git repo
        task.status = TaskStatus.committing
        task.log("Committing generated app to a fresh Git repo...")
        await git_ops.init_and_commit(workspace_path, task.prompt)
        task.log("Committed on branch 'main'.")

        # Create a GitHub repo and push (archival)
        task.status = TaskStatus.pushing
        task.log("Creating GitHub repo and pushing...")
        task.repo_url = await github_ops.create_and_push(workspace_path, task.prompt, task.id)
        task.log(f"Pushed to {task.repo_url}")

        # Deploy to Vercel and capture the live URL
        task.status = TaskStatus.deploying
        task.log("Deploying to Vercel (building remotely, this can take a minute)...")
        task.deployment_url = await vercel_ops.deploy(workspace_path)

        task.status = TaskStatus.completed
        task.log(f"Deployment complete: {task.deployment_url}")
    except Exception as exc:  # noqa: BLE001 - any failure must land on the task
        task.status = TaskStatus.failed
        task.error = str(exc)
        task.log(f"Task failed: {exc}")
