"""GitHub ops tests. The API call and git push are mocked — no network, no token needed
(except the env var the push path reads, which we set to a fake)."""

import asyncio
from pathlib import Path

import pytest

from services import github_ops


def test_slugify_basic():
    assert (
        github_ops._slugify("A Landing Page for a Boxing Gym!")
        == "a-landing-page-for-a-boxing-gym"
    )


def test_slugify_collapses_and_trims():
    assert github_ops._slugify("   multiple   spaces!!  ") == "multiple-spaces"


def test_slugify_truncates():
    assert len(github_ops._slugify("x" * 100)) <= 40


def test_create_and_push_uses_transient_token_url(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_fake")

    async def fake_create(name, *, private=False):
        return {
            "clone_url": f"https://github.com/me/{name}.git",
            "html_url": f"https://github.com/me/{name}",
        }

    monkeypatch.setattr(github_ops, "_create_repo", fake_create)

    calls: list[list[str]] = []

    async def fake_run(cmd, cwd=None):
        calls.append(cmd)

    monkeypatch.setattr(github_ops.shell, "run", fake_run)

    url = asyncio.run(
        github_ops.create_and_push(Path("/tmp/x"), "a boxing gym!", "8b611823-abcd")
    )

    assert url == "https://github.com/me/a-boxing-gym-8b611823"
    push = next(c for c in calls if len(c) > 1 and c[1] == "push")
    assert push[2].startswith("https://x-access-token:ghp_fake@github.com/me/")
    remote = next(c for c in calls if len(c) > 1 and c[1] == "remote")
    assert "x-access-token" not in " ".join(remote)  # clean remote, no token on disk


def test_missing_token_raises(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with pytest.raises(ValueError):
        asyncio.run(github_ops._create_repo("x"))
