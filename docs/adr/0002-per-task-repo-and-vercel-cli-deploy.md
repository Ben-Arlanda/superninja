# 0002 — Fresh GitHub repo per Task + Vercel CLI direct deploy

- **Status:** Accepted
- **Date:** 2026-05-31

## Context

Each Task must end with the Generated App archived on GitHub and live at a Vercel
Deployment URL. Two related choices shape the `committing → pushing → deploying`
steps:

**1. Shared infrastructure vs. per-Task infrastructure.**
A single shared GitHub repo + Vercel project is simplest to set up once, but every
Task overwrites the last, the apps are not independent, and two concurrent Tasks
conflict on the same repo. The forcing scenario: running "boxing gym" then
"coffee shop" should yield *two* live sites, not one that clobbered the other.

**2. How Vercel deploys.**
- *Vercel Git integration* (push auto-triggers a build) requires the Vercel–GitHub
  app installed, a project created and linked per Task, and polling Vercel's API to
  learn when the build finished and what the URL is — many moving parts.
- *Vercel CLI direct deploy* uploads the workspace files directly and prints the
  Deployment URL to stdout, with no project pre-linking and no polling. It also
  decouples deploy from GitHub entirely.

## Decision

- Each Task creates its **own fresh GitHub repo** (via the GitHub API, under the
  personal account) and writes/commits/pushes into it. Repos are created per Task,
  not reused.
- Deploy via the **Vercel CLI** (`vercel deploy --yes --token=…`) run as a
  subprocess from the Task's workspace directory; capture the Deployment URL from
  stdout.
- GitHub push and Vercel deploy are **independent** steps: the push is archival
  ("the code lives on GitHub"); the deploy is what produces the URL. The CLI deploy
  does not depend on the push having happened.

## Consequences

- **Positive:** Every Prompt becomes an independent, reproducible live site at its
  own URL. Concurrent Tasks never collide. The deploy path is the simplest reliable
  way to obtain a URL — no Git–Vercel app, no per-Task project linking, no polling.
  Push and deploy can fail or be reasoned about independently.
- **Negative / accepted cost:** GitHub repos and Vercel deployments accumulate under
  the account; cleanup is a deferred concern. Creating a repo per Task needs a PAT
  with repo-creation scope. Deploying via the CLI introduces a Node + `vercel` CLI
  runtime dependency on the backend host (the alternative — Vercel's REST API from
  Python — was considered and deferred as more code for the MVP).
- **Reversibility:** Moving to shared infra or Git-integration deploy later is
  possible but would rewrite the `committing/pushing/deploying` steps, so the choice
  is recorded here.
