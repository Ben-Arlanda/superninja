"""Agent + workspace tests. The LLM call is mocked at the _request_page_tsx seam,
so these run with no API key and no network."""

import asyncio

import pytest

import config
from agents import page_generator
from services import workspace


# --- fence stripping + validation ---


def test_strip_fences_removes_tsx_fence():
    fenced = "```tsx\nexport default function Page() { return null; }\n```"
    assert (
        page_generator._strip_fences(fenced)
        == "export default function Page() { return null; }"
    )


def test_strip_fences_leaves_plain_code():
    code = "export default function Page() { return null; }"
    assert page_generator._strip_fences(code) == code


def test_validate_rejects_empty():
    with pytest.raises(ValueError):
        page_generator._validate("")


def test_validate_rejects_missing_default_export():
    with pytest.raises(ValueError):
        page_generator._validate("const x = 1;")


# --- generate_page_code (LLM mocked) ---


def test_generate_page_code_strips_and_validates(monkeypatch):
    async def fake_request(_prompt):
        return "```tsx\nexport default function Page() { return <main/>; }\n```"

    monkeypatch.setattr(page_generator, "_request_page_tsx", fake_request)
    code = asyncio.run(page_generator.generate_page_code("a gym"))
    assert code == "export default function Page() { return <main/>; }"


def test_generate_page_code_raises_on_bad_output(monkeypatch):
    async def fake_request(_prompt):
        return "Sure! Here is your page."  # no default export

    monkeypatch.setattr(page_generator, "_request_page_tsx", fake_request)
    with pytest.raises(ValueError):
        asyncio.run(page_generator.generate_page_code("a gym"))


# --- workspace (real scaffold copy into a temp dir) ---


def test_create_workspace_copies_scaffold_and_writes_page(monkeypatch, tmp_path):
    monkeypatch.setattr(config.settings, "workspace_dir", tmp_path)

    ws = workspace.create_workspace("task-123")
    assert (ws / "package.json").exists()
    assert (ws / "app" / "layout.tsx").exists()

    workspace.write_page(ws, "export default function Page() { return null; }")
    assert "export default" in (ws / "app" / "page.tsx").read_text()
