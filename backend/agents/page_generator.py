"""The Agent — generates a landing page's `app/page.tsx` with Claude (Opus 4.8).

Per ADR 0001 (hybrid generation), the LLM produces ONLY the page component; the rest
of the app is the fixed scaffold. We ask for raw TSX, defensively strip any stray
code fences, and sanity-check the result before it's written to disk.
"""

from anthropic import AsyncAnthropic

from config import settings

_SYSTEM_PROMPT = """You are an expert frontend engineer. You generate a single \
Next.js App Router page component: the contents of `app/page.tsx`.

Output ONLY the complete contents of that file — no markdown code fences, no \
commentary, no explanation. Just raw TSX.

Hard requirements:
- Export a single default React component: `export default function Page() { ... }`.
- Style EXCLUSIVELY with Tailwind CSS utility classes. Do not import any package \
(no `next/image`, no icon libraries, no fonts). You should need zero import statements.
- For any visuals use Tailwind, emoji, or inline SVG only — never external image URLs.
- Valid, compilable TSX with no TypeScript errors. Do not add `"use client"` unless \
you actually use hooks or event handlers.
- Produce a polished, bespoke, multi-section landing page tailored to the request \
(hero, feature/content sections, a call-to-action, and a footer).

Return only the file contents."""

# Lazily-constructed client so importing this module never requires an API key
# (keeps the mocked test suite key-free). The real key is read from the env by the SDK.
_client: AsyncAnthropic | None = None


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic()
    return _client


async def _request_page_tsx(prompt: str) -> str:
    """Raw Claude call. Streams the response and returns the model's text output.

    This thin wrapper is the LLM seam — tests monkeypatch it to avoid real API calls.
    """
    client = _get_client()
    async with client.messages.stream(
        model=settings.anthropic_model,
        max_tokens=20000,
        thinking={"type": "adaptive"},
        system=[
            {
                "type": "text",
                "text": _SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": f"Build a landing page: {prompt}"}],
    ) as stream:
        message = await stream.get_final_message()

    # With adaptive thinking, content may include thinking blocks (empty text by
    # default) — keep only the visible text blocks.
    return "".join(b.text for b in message.content if b.type == "text").strip()


async def generate_page_code(prompt: str) -> str:
    """Generate clean, validated TSX for app/page.tsx from a natural-language prompt."""
    raw = await _request_page_tsx(prompt)
    code = _strip_fences(raw)
    _validate(code)
    return code


def _strip_fences(text: str) -> str:
    """Remove a leading ```/```tsx fence and trailing ``` if the model added them."""
    t = text.strip()
    if t.startswith("```"):
        lines = t.splitlines()
        lines = lines[1:]  # drop the opening fence line
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]  # drop the closing fence
        t = "\n".join(lines)
    return t.strip()


def _validate(code: str) -> None:
    """Cheap sanity checks — fail early with a clear reason rather than deploy garbage."""
    if not code:
        raise ValueError("Claude returned empty page content")
    if "export default" not in code:
        raise ValueError("Generated page has no default export — not a valid component")
