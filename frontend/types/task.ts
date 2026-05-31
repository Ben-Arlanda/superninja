// Mirrors the backend Task model (the typed contract between frontend and API).

export type TaskStatus =
  | "pending"
  | "running"
  | "generating_files"
  | "committing"
  | "pushing"
  | "deploying"
  | "completed"
  | "failed";

export interface LogEntry {
  timestamp: string;
  message: string;
}

export interface Task {
  id: string;
  prompt: string;
  status: TaskStatus;
  logs: LogEntry[];
  deployment_url: string | null;
  repo_url: string | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}
