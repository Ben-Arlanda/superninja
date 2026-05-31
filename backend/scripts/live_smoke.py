"""Manual live test — actually call Claude and print the generated page.

Run from backend/ with ANTHROPIC_API_KEY set in backend/.env:
    ./venv/bin/python scripts/live_smoke.py "a landing page for a boxing gym"
"""

import asyncio
import sys
from pathlib import Path

# Make backend/ importable when run as a plain script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.page_generator import generate_page_code  # noqa: E402


async def main() -> None:
    prompt = sys.argv[1] if len(sys.argv) > 1 else "a landing page for a boxing gym"
    print(f"Prompt: {prompt}\nCalling Opus 4.8 (this can take a while)...\n")
    code = await generate_page_code(prompt)
    print(code)
    print(f"\n--- {len(code)} characters ---")


if __name__ == "__main__":
    asyncio.run(main())
