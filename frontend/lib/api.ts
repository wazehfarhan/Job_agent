// Typed API client. Every path here is relative to the API prefix (/api).
// NEXT_PUBLIC_API_URL must be reachable from the browser (localhost for dev).
import { clearToken, getToken } from "./auth";
import type {
  Application,
  DiscoverResult,
  Health,
  Job,
  JobList,
  ProfileOut,
  Resume,
  ResumeDetail,
  RuntimeSettings,
  StatusEvent,
  Token,
  UserOut,
} from "@/types/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

type Options = RequestInit & { skipAuthRedirect?: boolean };

export async function apiFetch<T>(path: string, options: Options = {}): Promise<T> {
  const { skipAuthRedirect, ...rest } = options;
  const token = getToken();
  const headers: Record<string, string> = { ...(rest.headers as Record<string, string>) };
  // FormData / URLSearchParams set their own correct Content-Type.
  const isSelfTypingBody = rest.body instanceof FormData || rest.body instanceof URLSearchParams;
  if (!isSelfTypingBody) headers["Content-Type"] = "application/json";
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_URL}/api${path}`, { ...rest, headers });

  if (res.status === 401 && !skipAuthRedirect) {
    clearToken();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new ApiError(401, "Session expired — please log in again");
  }
  if (!res.ok) {
    const payload = await res.json().catch(() => null);
    const detail = payload?.detail;
    throw new ApiError(res.status, typeof detail === "string" ? detail : `HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export async function apiHealth(): Promise<Health> {
  const res = await fetch(`${API_URL}/api/health`);
  if (!res.ok) throw new ApiError(res.status, `HTTP ${res.status}`);
  return (await res.json()) as Health;
}

export const api = {
  // Auth
  register: (email: string, password: string) =>
    apiFetch<UserOut>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  login: (email: string, password: string) =>
    apiFetch<Token>(
      "/auth/login",
      {
        method: "POST",
        body: new URLSearchParams({ username: email, password }),
        skipAuthRedirect: true, // a wrong password must show an error, not bounce
      },
    ),
  me: () => apiFetch<UserOut>("/auth/me"),

  // Profile
  getProfile: () => apiFetch<ProfileOut>("/profile/me"),
  updateProfile: (payload: ProfileOut) =>
    apiFetch<ProfileOut>("/profile/me", { method: "PUT", body: JSON.stringify(payload) }),

  // Resumes
  listResumes: () => apiFetch<Resume[]>("/resumes"),
  uploadResume: (label: string, file: File) => {
    const form = new FormData();
    form.append("label", label);
    form.append("file", file);
    return apiFetch<ResumeDetail>("/resumes", { method: "POST", body: form });
  },
  setDefaultResume: (id: string) =>
    apiFetch<Resume>(`/resumes/${id}/set-default`, { method: "PUT" }),
  getResume: (id: string) => apiFetch<ResumeDetail>(`/resumes/${id}`),
  deleteResume: (id: string) => apiFetch<void>(`/resumes/${id}`, { method: "DELETE" }),

  // Jobs
  listJobs: (limit = 50, offset = 0) =>
    apiFetch<JobList>(`/jobs?limit=${limit}&offset=${offset}`),
  discover: () => apiFetch<DiscoverResult>("/jobs/discover", { method: "POST" }),
  extractJob: (id: string) => apiFetch<Job>(`/jobs/${id}/extract`, { method: "POST" }),
  extractPending: (limit = 25) =>
    apiFetch<JobList>(`/jobs/extract-pending?limit=${limit}`, { method: "POST" }),

  // Applications
  listApplications: () => apiFetch<Application[]>("/applications"),
  createApplication: (jobId: string) =>
    apiFetch<Application>("/applications", {
      method: "POST",
      body: JSON.stringify({ job_id: jobId }),
    }),
  getApplication: (id: string) => apiFetch<Application>(`/applications/${id}`),
  transition: (id: string, status: string, note: string | null) =>
    apiFetch<Application>(`/applications/${id}/transition`, {
      method: "POST",
      body: JSON.stringify({ status, note }),
    }),
  matchApplication: (id: string) =>
    apiFetch<Application>(`/applications/${id}/match`, { method: "POST" }),
  listEvents: (id: string) => apiFetch<StatusEvent[]>(`/applications/${id}/events`),

  // Settings
  getSettings: () => apiFetch<RuntimeSettings>("/settings"),
};