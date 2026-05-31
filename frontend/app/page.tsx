"use client";

import { useEffect, useRef, useState } from "react";
import { createTask, getTask } from "@/lib/api";
import type { Task, TaskStatus } from "@/types/task";

// Lifecycle order, and the subset we show as visible "stages" in the stepper.
const ORDER: TaskStatus[] = [
  "pending",
  "running",
  "generating_files",
  "committing",
  "pushing",
  "deploying",
  "completed",
];
const STAGES: { key: TaskStatus; label: string }[] = [
  { key: "running", label: "Start" },
  { key: "generating_files", label: "Generate" },
  { key: "committing", label: "Commit" },
  { key: "pushing", label: "Push" },
  { key: "deploying", label: "Deploy" },
  { key: "completed", label: "Live" },
];

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [task, setTask] = useState<Task | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const logRef = useRef<HTMLDivElement>(null);

  const running = !!task && task.status !== "completed" && task.status !== "failed";

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const p = prompt.trim();
    if (!p || submitting || running) return;
    setSubmitting(true);
    setApiError(null);
    setTask(null);
    try {
      setTask(await createTask(p));
    } catch {
      setApiError("Couldn't reach the SuperNinja API. Is the backend running on :8000?");
    } finally {
      setSubmitting(false);
    }
  }

  // Poll while a task is running; stop once it's terminal.
  useEffect(() => {
    if (!task || !running) return;
    const id = task.id;
    const timer = setInterval(async () => {
      try {
        setTask(await getTask(id));
      } catch {
        /* transient network hiccup — keep polling */
      }
    }, 1200);
    return () => clearInterval(timer);
  }, [task?.id, task?.status, running]);

  // Keep the log view scrolled to the newest line.
  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight });
  }, [task?.logs.length]);

  const currentIndex = task ? ORDER.indexOf(task.status) : -1;

  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-3xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-2 font-mono text-sm tracking-[0.3em] text-fg">
          <span className="text-accent">✦</span> SUPERNINJA
        </div>
        <span className="font-mono text-[0.7rem] uppercase tracking-[0.25em] text-muted">
          prompt → deployed app
        </span>
      </header>

      <main className="mx-auto max-w-3xl px-6 pb-24">
        <section className="pt-10 pb-9">
          <h1 className="font-display text-5xl leading-[1.04] tracking-tight text-fg sm:text-6xl">
            Ship an app
            <br />
            <span className="text-accent">from a sentence.</span>
          </h1>
          <p className="mt-6 max-w-md text-lg leading-relaxed text-muted">
            Describe what you want. SuperNinja generates it, commits it, pushes it to
            GitHub, and deploys it live to Vercel — while you watch.
          </p>
        </section>

        <form onSubmit={onSubmit}>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Build me a landing page for a boxing gym…"
            rows={3}
            disabled={submitting || running}
            className="w-full resize-none rounded-xl border border-border bg-surface px-5 py-4 font-mono text-sm text-fg outline-none transition placeholder:text-muted/50 focus:border-accent/60 disabled:opacity-60"
          />
          <div className="mt-3 flex items-center justify-between">
            <span className="font-mono text-xs text-muted">
              {running ? "build in progress…" : "Autonomous agent · Next.js · Vercel"}
            </span>
            {task && !running ? (
              <button
                type="button"
                onClick={() => {
                  setTask(null);
                  setPrompt("");
                }}
                className="cursor-pointer rounded-full border border-border px-5 py-2 font-mono text-xs uppercase tracking-[0.2em] text-fg transition hover:border-accent/60"
              >
                New build
              </button>
            ) : (
              <button
                type="submit"
                disabled={submitting || running || !prompt.trim()}
                className="cursor-pointer rounded-full bg-accent px-6 py-2.5 font-mono text-xs font-semibold uppercase tracking-[0.2em] text-bg transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {submitting ? "Launching…" : "Build it →"}
              </button>
            )}
          </div>
        </form>

        {apiError && (
          <p className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 font-mono text-sm text-red-300">
            {apiError}
          </p>
        )}

        {task && (
          <section className="mt-10" style={{ animation: "fade 0.4s ease both" }}>
            {/* status stepper */}
            <div className="flex flex-wrap items-center gap-x-3 gap-y-3">
              {STAGES.map((stage, i) => {
                const idx = ORDER.indexOf(stage.key);
                const done = task.status === "completed" || currentIndex > idx;
                const active = task.status === stage.key && task.status !== "completed";
                return (
                  <div key={stage.key} className="flex items-center gap-2">
                    <span
                      className={[
                        "h-2 w-2 rounded-full transition",
                        active
                          ? "animate-pulse bg-accent"
                          : done
                            ? "bg-accent"
                            : task.status === "failed"
                              ? "bg-red-500/40"
                              : "bg-border",
                      ].join(" ")}
                    />
                    <span
                      className={[
                        "font-mono text-xs uppercase tracking-[0.2em]",
                        active ? "text-accent" : done ? "text-fg" : "text-muted",
                      ].join(" ")}
                    >
                      {stage.label}
                    </span>
                    {i < STAGES.length - 1 && <span className="text-muted/30">/</span>}
                  </div>
                );
              })}
            </div>

            {/* log terminal */}
            <div
              ref={logRef}
              className="mt-6 max-h-64 overflow-y-auto rounded-xl border border-border bg-black/40 p-4 font-mono text-xs leading-relaxed"
            >
              {task.logs.length === 0 ? (
                <span className="text-muted">waiting…</span>
              ) : (
                task.logs.map((log, i) => (
                  <div key={i} className="flex gap-3">
                    <span className="shrink-0 text-muted/50">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                    <span className="text-fg/90">{log.message}</span>
                  </div>
                ))
              )}
            </div>

            {/* result */}
            {task.status === "completed" && task.deployment_url && (
              <div className="mt-6 flex flex-wrap gap-3">
                <a
                  href={task.deployment_url}
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-full bg-accent px-6 py-3 font-mono text-xs font-semibold uppercase tracking-[0.2em] text-bg transition hover:brightness-110"
                >
                  View live site ↗
                </a>
                {task.repo_url && (
                  <a
                    href={task.repo_url}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-full border border-border px-6 py-3 font-mono text-xs uppercase tracking-[0.2em] text-fg transition hover:border-accent/60"
                  >
                    View code ↗
                  </a>
                )}
              </div>
            )}
            {task.status === "failed" && (
              <p className="mt-6 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 font-mono text-sm text-red-300">
                {task.error ?? "The build failed."}
              </p>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
