"""Central configuration.

Loads backend/.env into the process environment (so the Anthropic SDK can read
ANTHROPIC_API_KEY on its own) and exposes a single `settings` object with the model
id and the filesystem paths the Agent uses.
"""

from pathlib import Path

from dotenv import load_dotenv

# Resolve paths relative to this file so it works regardless of the current
# working directory. BACKEND_DIR is .../superninja/backend.
BACKEND_DIR = Path(__file__).resolve().parent

# Load backend/.env into os.environ. The anthropic SDK reads ANTHROPIC_API_KEY
# from there automatically — we never pass the key around by hand.
load_dotenv(BACKEND_DIR / ".env")


class Settings:
    """Static app configuration. (No secrets stored here — those live in .env.)"""

    # Exact Opus 4.8 model id. Must not carry a date suffix.
    anthropic_model = "claude-opus-4-8"

    # The known-good Next.js scaffold copied for every Task.
    template_dir = BACKEND_DIR / "templates" / "landing-page"

    # Where each Task's generated app is written: workspace/{task_id}/
    workspace_dir = BACKEND_DIR / "workspace"


settings = Settings()
