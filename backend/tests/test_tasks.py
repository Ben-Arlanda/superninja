"""Task lifecycle + HTTP contract tests.

The runner now calls a real LLM during generating_files, so pipeline tests mock the
Agent and filesystem to stay hermetic (no API key, no network, no disk writes under
backend/workspace). Run from backend/:  python -m pytest
"""

import asyncio

import pytest
from fastapi.testclient import TestClient

from main import app
from models.task import Task, TaskStatus
from services import task_runner

client = TestClient(app)

_FAKE_TSX = "export default function Page() {\n  return <main>Hi</main>;\n}\n"


@pytest.fixture
def instant_sleep(monkeypatch):
    """Make the runner's stub delays instant."""

    async def _noop(*_args, **_kwargs):
        return None

    monkeypatch.setattr(task_runner.asyncio, "sleep", _noop)


@pytest.fixture
def fake_generation(monkeypatch, tmp_path):
    """Replace the real Agent + filesystem writes so the pipeline runs hermetically."""

    async def fake_generate(_prompt):
        return _FAKE_TSX

    monkeypatch.setattr(task_runner, "generate_page_code", fake_generate)

    def fake_create_workspace(task_id):
        (tmp_path / task_id / "app").mkdir(parents=True, exist_ok=True)
        return tmp_path / task_id

    monkeypatch.setattr(task_runner.workspace, "create_workspace", fake_create_workspace)

    def fake_write_page(path, code):
        (path / "app" / "page.tsx").write_text(code)

    monkeypatch.setattr(task_runner.workspace, "write_page", fake_write_page)

    async def fake_commit(_path, _prompt):
        return None

    monkeypatch.setattr(task_runner.git_ops, "init_and_commit", fake_commit)


# --- Runner unit tests (lifecycle correctness) ---


def test_runner_walks_full_lifecycle(instant_sleep, fake_generation):
    task = Task(prompt="Build a boxing gym landing page")
    assert task.status == TaskStatus.pending

    asyncio.run(task_runner.run_task(task))

    assert task.status == TaskStatus.completed
    assert task.deployment_url and task.deployment_url.startswith("https://")
    assert task.error is None
    messages = [entry.message for entry in task.logs]
    assert any("started" in m for m in messages)
    assert any("Generating" in m for m in messages)
    assert any("Committing" in m for m in messages)
    assert any("Pushing" in m for m in messages)
    assert any("Deploying" in m for m in messages)
    assert any("complete" in m for m in messages)


def test_runner_marks_failed_when_generation_raises(instant_sleep, monkeypatch):
    async def boom(_prompt):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(task_runner, "generate_page_code", boom)
    monkeypatch.setattr(task_runner.workspace, "create_workspace", lambda _id: None)

    task = Task(prompt="anything")
    asyncio.run(task_runner.run_task(task))

    assert task.status == TaskStatus.failed
    assert "kaboom" in (task.error or "")
    assert task.deployment_url is None


# --- Endpoint tests (HTTP contract) ---


def test_create_task_returns_201_and_pending(instant_sleep, fake_generation):
    resp = client.post("/tasks", json={"prompt": "Build a coffee shop landing page"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"]
    assert body["prompt"] == "Build a coffee shop landing page"
    assert body["status"] == "pending"


def test_get_task_after_completion(instant_sleep, fake_generation):
    created = client.post("/tasks", json={"prompt": "Build a SaaS landing page"}).json()
    resp = client.get(f"/tasks/{created['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "completed"
    assert body["deployment_url"].startswith("https://")


def test_get_unknown_task_returns_404():
    assert client.get("/tasks/does-not-exist").status_code == 404


def test_empty_prompt_returns_422():
    assert client.post("/tasks", json={"prompt": ""}).status_code == 422
