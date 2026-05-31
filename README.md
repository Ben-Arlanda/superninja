# SuperNinja

**Describe an app in a sentence. SuperNinja generates it, ships it to GitHub, and deploys it live — while you watch.**

SuperNinja is a Mini Agentic AI Platform: you submit a natural-language prompt like
_"Build me a landing page for a boxing gym"_, and an AI agent turns it into a real,
deployed web app — returning a live URL.

```
prompt  →  generate (Claude)  →  commit (git)  →  push (GitHub)  →  deploy (Vercel)  →  live URL
```

---

## What it does

A single page lets you type a prompt and watch the pipeline run in real time — a status
stepper and a live log stream advance through each stage until a **live site** and its
**source repo** are linked back to you.

Each prompt produces an **independent** artifact: its own fresh GitHub repository and its
own Vercel deployment.

### The Task lifecycle

A prompt creates a **Task**, which moves through these statuses:

`pending → running → generating_files → committing → pushing → deploying → completed`
(or `failed`, with the reason recorded).

---

## How it works

- **Async pipeline.** `POST /tasks` returns immediately with a `pending` task; the work
  runs in the background (FastAPI `BackgroundTasks`). The frontend polls `GET /tasks/{id}`
  every ~1.2s to render live status + logs. No database — tasks live in memory for the
  session.
- **Hybrid generation** ([ADR 0001](docs/adr/0001-hybrid-generation-scaffold-plus-llm-page.md)).
  The generated app is a **fixed, known-good Next.js scaffold** where Claude generates
  only `app/page.tsx`. This keeps deploys reliable: an LLM mistake can only affect one
  file inside a shell that always builds.
- **Per-task repo + CLI deploy** ([ADR 0002](docs/adr/0002-per-task-repo-and-vercel-cli-deploy.md)).
  Every Task gets a fresh GitHub repo (pushed for archival) and is deployed directly from
  its workspace via the Vercel CLI (decoupled from GitHub).

See [`CONTEXT.md`](CONTEXT.md) for the domain glossary.

---

## Tech stack

| Layer    | Tech                                                     |
| -------- | -------------------------------------------------------- |
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS v4        |
| Backend  | FastAPI (Python 3.13), Pydantic, async `BackgroundTasks` |
| Agent    | Anthropic **Claude Opus 4.8** (`anthropic` SDK)          |
| Delivery | `git` CLI, GitHub REST API, Vercel CLI                   |

---

## Project structure

```
superninja/
├── backend/
│   ├── main.py                 # FastAPI app + CORS + /health
│   ├── routers/tasks.py        # POST /tasks, GET /tasks/{id}
│   ├── models/task.py          # Task, TaskStatus, LogEntry (Pydantic)
│   ├── services/
│   │   ├── store.py            # in-memory task store
│   │   ├── task_runner.py      # the pipeline orchestrator
│   │   ├── workspace.py        # copy scaffold → workspace/{id}/
│   │   ├── git_ops.py          # git init + commit
│   │   ├── github_ops.py       # create repo + push (GitHub API)
│   │   └── vercel_ops.py       # vercel deploy + capture URL
│   ├── agents/page_generator.py# Claude call → app/page.tsx
│   ├── templates/landing-page/ # the fixed Next.js scaffold
│   ├── utils/shell.py          # async command runner (non-blocking)
│   └── tests/                  # pytest suite
├── frontend/
│   ├── app/page.tsx            # the single-page UI (prompt → live status → links)
│   ├── lib/api.ts              # createTask / getTask
│   └── types/task.ts           # shared Task type
└── docs/adr/                   # architecture decision records
```

---

## Running it locally

### Prerequisites

- Python 3.13, Node.js 20+
- `git`, and the Vercel CLI (`npm i -g vercel`)
- Accounts/keys: Anthropic, GitHub (classic PAT with `repo` scope), Vercel

### 1. Backend

```bash
cd backend
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# configure secrets
cp .env.example .env          # then edit .env:
#   ANTHROPIC_API_KEY=sk-ant-...
#   GITHUB_TOKEN=ghp_...
#   VERCEL_TOKEN=...
#   VERCEL_SCOPE=your-team-slug

./venv/bin/uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev                    # http://localhost:3000
```

Open **http://localhost:3000**, type a prompt, and click **Build it**.

> `.env` and `backend/workspace/` are git-ignored — secrets and generated apps never get
> committed.

---

## Testing

```bash
cd backend
./venv/bin/python -m pytest
```

The suite mocks the external services (Claude, GitHub, Vercel) so it runs fast, offline,
and free.

---

## Known limitations

This is an MVP, scoped deliberately:

- **In-memory store** — tasks are lost on server restart (no persistence/history).
- **Generated apps are single-page landing sites** — the scaffold is fixed (see ADR 0001).
- **Artifacts accumulate** — each run leaves a GitHub repo and a Vercel project behind.

---

## API

| Method | Path          | Description                                                              |
| ------ | ------------- | ------------------------------------------------------------------------ |
| `POST` | `/tasks`      | Create a task from `{ "prompt": "..." }`; returns the `pending` task     |
| `GET`  | `/tasks/{id}` | Current task state (status, logs, `repo_url`, `deployment_url`, `error`) |
| `GET`  | `/health`     | Health check                                                             |
