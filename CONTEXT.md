# SuperNinja — Context

## What this is

SuperNinja is a **Mini NinjaTech MVP**. A user submits a natural-language **Prompt**
(e.g. "Build me a landing page for a boxing gym"); the system then autonomously
generates a web application, commits it to Git, pushes to GitHub, deploys to Vercel,
and returns a live **Deployment URL**. It demonstrates the core idea behind
NinjaTech AI: an agent that turns plain-language intent into a deployed artifact.

## Glossary

These are domain terms — the shared language. They are intentionally free of
implementation detail.

### Task
A single end-to-end run triggered by one **Prompt**. It is the unit of work the
system tracks from submission through to deployment (or failure). A Task carries its
originating Prompt, a **Status**, an ordered log of what happened, and — once
deployed — a **Deployment URL**.

### Prompt
The user's natural-language instruction describing the application they want built.
The input that creates a Task.

### Status (Task lifecycle)
Where a Task sits in its lifecycle. Exactly one of, in normal forward order:

| Status | Meaning |
| --- | --- |
| `pending` | Created, not yet started. |
| `running` | Execution has begun. |
| `generating_files` | Producing the target application's source files. |
| `committing` | Recording the generated files into Git. |
| `pushing` | Uploading the commit to GitHub. |
| `deploying` | Triggering and awaiting a Vercel deployment. |
| `completed` | Finished successfully; a Deployment URL is available. |
| `failed` | Stopped before completion; the failure reason is recorded. |

A Task that fails records *why* (a failure reason), so the cause never has to be
scraped out of the log.

### Deployment URL
The public Vercel URL of the generated application. Absent until a Task deploys
successfully; populated when the Task reaches `completed`.

### Generated App
The application a Task produces from its Prompt — a standalone, deployable web app
(for the MVP, a single-page landing site). It is independent and disposable: each
Task creates its own, with its own source repository and its own live Deployment URL.
Distinct from **SuperNinja** itself, which is the platform that produces it.

### Workspace
The directory into which a Task writes its Generated App before it is committed and
deployed. Each Task gets its own isolated space.

### Agent
The component that turns a Prompt into a Generated App and drives the Task through its
lifecycle — generating the app (AI-assisted), then sequencing the
commit → push → deploy steps.
