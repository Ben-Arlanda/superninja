"""Phase 1 tests: the stub runner's lifecycle + the HTTP contract.

Run from the backend/ directory:  python -m pytest
"""

import asyncio

import pytest
from fastapi.testclient import TestClient

from main import app
from models.task import Task, TaskStatus
from services import task_runner

client = TestClient(app)


@pytest.fixture
def instant_sleep(monkeypatch):
    """Make the runner's delays instant so tests don't actually wait."""

    async def _noop(*_args, **_kwargs):
        return None

    monkeypatch.setattr(task_runner.asyncio, "sleep", _noop)


# --- Runner unit tests (this is where lifecycle correctness lives) ---


def test_runner_walks_full_lifecycle(instant_sleep):
    task = Task(prompt="Build a boxing gym landing page")
    assert task.status == TaskStatus.pending  # starts pending

    asyncio.run(task_runner.run_task(task))

    assert task.status == TaskStatus.completed
    assert task.deployment_url and task.deployment_url.startswith("https://")
    assert task.error is None
    # Every step ran (its log line is present, in order).
    messages = [entry.message for entry in task.logs]
    assert any("started" in m for m in messages)
    assert any("Generating" in m for m in messages)
    assert any("Committing" in m for m in messages)
    assert any("Pushing" in m for m in messages)
    assert any("Deploying" in m for m in messages)
    assert any("complete" in m for m in messages)


def test_runner_marks_failed_on_exception(monkeypatch):
    async def boom(*_args, **_kwargs):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(task_runner.asyncio, "sleep", boom)

    task = Task(prompt="anything")
    asyncio.run(task_runner.run_task(task))

    assert task.status == TaskStatus.failed
    assert "kaboom" in (task.error or "")
    assert task.deployment_url is None


# --- Endpoint tests (the HTTP contract) ---


def test_create_task_returns_201_and_pending(instant_sleep):
    resp = client.post("/tasks", json={"prompt": "Build a coffee shop landing page"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"]
    assert body["prompt"] == "Build a coffee shop landing page"
    assert body["status"] == "pending"  # serialized before the runner advanced it


def test_get_task_after_completion(instant_sleep):
    created = client.post("/tasks", json={"prompt": "Build a SaaS landing page"}).json()
    # TestClient already ran the background task to completion during the POST above.
    resp = client.get(f"/tasks/{created['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "completed"
    assert body["deployment_url"].startswith("https://")
    assert len(body["logs"]) >= 1


def test_get_unknown_task_returns_404():
    resp = client.get("/tasks/does-not-exist")
    assert resp.status_code == 404


def test_empty_prompt_returns_422():
    resp = client.post("/tasks", json={"prompt": ""})
    assert resp.status_code == 422
