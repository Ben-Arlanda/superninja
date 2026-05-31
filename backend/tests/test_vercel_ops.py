"""Vercel ops tests. The CLI is mocked (no install, no network)."""

import asyncio
from pathlib import Path

import pytest

from services import vercel_ops

_SAMPLE = """Vercel CLI 39.0.0
Inspect: https://vercel.com/me/proj/abc123 [2s]
Production: https://my-app-8a34427a.vercel.app [38s]
"""


def test_extract_url_finds_vercel_app():
    assert vercel_ops._extract_url(_SAMPLE) == "https://my-app-8a34427a.vercel.app"


def test_extract_url_raises_when_absent():
    with pytest.raises(RuntimeError):
        vercel_ops._extract_url("no deployment url here")


def test_deploy_runs_prod_and_returns_url(monkeypatch):
    monkeypatch.setenv("VERCEL_TOKEN", "vc_fake")
    captured: dict = {}

    async def fake_run(cmd, cwd=None, secret=None):
        captured["cmd"] = cmd
        captured["secret"] = secret

        class _Result:
            stdout = "Production: https://x-8a34427a.vercel.app\n"
            stderr = ""

        return _Result()

    monkeypatch.setattr(vercel_ops.shell, "run", fake_run)

    url = asyncio.run(vercel_ops.deploy(Path("/tmp/ws")))

    assert url == "https://x-8a34427a.vercel.app"
    assert captured["cmd"][:4] == ["vercel", "deploy", "--prod", "--yes"]
    assert "vc_fake" in captured["cmd"]
    assert captured["secret"] == "vc_fake"  # so a failure redacts the token


def test_deploy_passes_scope_when_set(monkeypatch):
    monkeypatch.setenv("VERCEL_TOKEN", "vc_fake")
    monkeypatch.setenv("VERCEL_SCOPE", "my-team")
    captured: dict = {}

    async def fake_run(cmd, cwd=None, secret=None):
        captured["cmd"] = cmd

        class _Result:
            stdout = "https://x.vercel.app"
            stderr = ""

        return _Result()

    monkeypatch.setattr(vercel_ops.shell, "run", fake_run)
    asyncio.run(vercel_ops.deploy(Path("/tmp/ws")))
    assert "--scope" in captured["cmd"]
    assert "my-team" in captured["cmd"]


def test_missing_token_raises(monkeypatch):
    monkeypatch.delenv("VERCEL_TOKEN", raising=False)
    with pytest.raises(ValueError):
        asyncio.run(vercel_ops.deploy(Path("/tmp/ws")))
