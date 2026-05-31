"""Data shapes for a Task — both validation (Pydantic) and serialization live here."""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    """Timezone-aware UTC 'now'. Used as the default for timestamps."""
    return datetime.now(timezone.utc)


class TaskStatus(str, Enum):
    """The lifecycle of a Task, in normal forward order.

    Subclassing `str` means each member serializes to its plain string value
    (e.g. "pending") in JSON, while still being a real enum in Python.
    """

    pending = "pending"
    running = "running"
    generating_files = "generating_files"
    committing = "committing"
    pushing = "pushing"
    deploying = "deploying"
    completed = "completed"
    failed = "failed"


class LogEntry(BaseModel):
    """One line in a Task's activity log."""

    timestamp: datetime = Field(default_factory=_utcnow)
    message: str


class TaskCreate(BaseModel):
    """Request body for creating a Task. Only the prompt is client-supplied.

    `min_length=1` rejects an empty prompt with a 422 automatically, so clients
    can't set id/status/logs themselves — those aren't on this model.
    """

    prompt: str = Field(min_length=1)


class Task(BaseModel):
    """The full Task record, stored in memory and returned by the API."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    prompt: str
    status: TaskStatus = TaskStatus.pending
    logs: list[LogEntry] = Field(default_factory=list)
    deployment_url: str | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    def log(self, message: str) -> None:
        """Append a log line and bump updated_at. One call per progress step."""
        self.logs.append(LogEntry(message=message))
        self.updated_at = _utcnow()
