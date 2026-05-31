"""In-memory task store.

A module-level dict is our 'database' for the MVP. The background runner and the
GET endpoint both hold a reference to the *same* Task object, so mutations made by
the runner are visible to the next GET with no re-saving. State is lost on restart,
which is acceptable for a single-session demo (see CONTEXT.md / build plan).
"""

from models.task import Task

_tasks: dict[str, Task] = {}


def save(task: Task) -> Task:
    """Insert (or replace) a task by its id."""
    _tasks[task.id] = task
    return task


def get(task_id: str) -> Task | None:
    """Return the task, or None if no task has that id."""
    return _tasks.get(task_id)
