"""Task HTTP endpoints: create one (and kick off its background run) and fetch one."""

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from models.task import Task, TaskCreate
from services import store
from services.task_runner import run_task

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=Task)
async def create_task(payload: TaskCreate, background_tasks: BackgroundTasks) -> Task:
    """Create a pending Task, schedule its background run, return it immediately.

    The task is serialized into the response *before* the runner mutates it, so the
    POST response shows status=pending. The client then polls GET /tasks/{id}.
    """
    task = Task(prompt=payload.prompt)
    store.save(task)
    background_tasks.add_task(run_task, task)
    return task


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str) -> Task:
    """Return the current state of a Task, or 404 if the id is unknown."""
    task = store.get(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task
