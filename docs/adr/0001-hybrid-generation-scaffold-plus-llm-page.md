# 0001 — Hybrid generation: fixed scaffold + LLM-generated page

- **Status:** Accepted
- **Date:** 2026-05-31

## Context

The Agent must turn a natural-language Prompt into a **Generated App** that
reliably builds and deploys on Vercel. A deployable Next.js app is not a single
file — it requires `package.json` (with valid dependency versions), `next.config`,
`tsconfig.json`, Tailwind config, `app/layout.tsx`, and `app/page.tsx`, all
mutually consistent. A single wrong dependency version or malformed config fails
the Vercel build.

There are three points on the spectrum of "how much does the LLM produce?":

1. **Pure template (no LLM)** — find-and-replace words in a fixed page. Deploys
   100% of the time, but it is not AI generation; it does not demonstrate the
   product concept.
2. **Full free-form LLM** — the LLM generates the entire app. Maximally authentic,
   but LLMs are excellent at *content* and unreliable at *plumbing*: they
   hallucinate package versions, omit config files, or mix routing conventions.
   When that happens the deploy fails for reasons unrelated to whether the
   pipeline works, turning every demo into a debugging session.
3. **Hybrid** — a fixed, hand-verified scaffold supplies the plumbing; the LLM
   generates only the landing-page component (`app/page.tsx`) from the Prompt.

This is an MVP whose goal is "a bespoke landing page reliably appears at a Vercel
URL." Reliability of the deploy is more valuable than the freedom to generate
arbitrary app structures.

## Decision

Use **hybrid generation**. Ship a fixed, deployable Next.js scaffold and have the
Agent (Claude) generate **only `app/page.tsx`** — the landing page's content,
layout, copy, and Tailwind styling — from the Prompt. All other files are static
and version-controlled with SuperNinja.

## Consequences

- **Positive:** The AI does the meaningful creative work (turning the Prompt into a
  real, bespoke page), so the product concept is genuinely demonstrated. The blast
  radius of any LLM error is contained to one file inside a shell that is
  guaranteed to build — worst case the page looks off, but it still deploys and
  still returns a URL.
- **Negative / accepted limitation:** The LLM cannot change the app's structure —
  no new routes, no new dependencies, no multi-page or stateful apps. SuperNinja
  can only ever produce single-page landing sites under this decision.
- **Reversibility:** Lifting the constraint (toward free-form generation) is
  possible later but would require a generation-validation loop — build the
  Generated App locally and only deploy if it compiles — to recover the reliability
  this decision buys cheaply. Revisit if the goal shifts from "reliable landing
  pages" to "arbitrary apps."
