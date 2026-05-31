import type { Task } from "@/types/task";

// Defaults to the local backend so it works with zero config in dev.
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function createTask(prompt: string): Promise<Task> {
  const res = await fetch(`${API_BASE}/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  if (!res.ok) throw new Error(`createTask failed: ${res.status}`);
  return res.json();
}

export async function getTask(id: string): Promise<Task> {
  const res = await fetch(`${API_BASE}/tasks/${id}`);
  if (!res.ok) throw new Error(`getTask failed: ${res.status}`);
  return res.json();
}
