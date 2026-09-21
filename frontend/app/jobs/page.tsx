"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useRequireAuth } from "@/lib/hooks";
import type { Job } from "@/types/api";

const STATUS_BADGE: Record<string, string> = {
  extracted: "bg-emerald-700",
  discovered: "bg-slate-700",
  duplicate: "bg-slate-700",
  matched: "bg-sky-700",
  ineligible: "bg-rose-800",
  expired: "bg-slate-700",
};

export default function JobsPage() {
  const ready = useRequireAuth();
  const router = useRouter();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [globalBusy, setGlobalBusy] = useState<string | null>(null);
  const [jobBusy, setJobBusy] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const list = await api.listJobs();
      setJobs(list.jobs);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load jobs");
    }
  }, []);

  useEffect(() => {
    if (ready) void load();
  }, [ready, load]);

  async function runGlobal(name: string, action: () => Promise<{ count?: number; discovered?: number }>) {
    setGlobalBusy(name);
    setError(null);
    setNotice(null);
    try {
      const result = await action();
      const count = result.discovered ?? result.count ?? 0;
      setNotice(`${name}: ${count} job(s) affected.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : `${name} failed`);
    } finally {
      setGlobalBusy(null);
    }
  }

  async function extractOne(job: Job) {
    setJobBusy(job.id);
    setError(null);
    try {
      await api.extractJob(job.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Extraction failed");
    } finally {
      setJobBusy(null);
    }
  }

  async function apply(job: Job) {
    setJobBusy(job.id);
    setError(null);
    try {
      await api.createApplication(job.id);
      router.push("/applications");
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setNotice("Application already exists for this job.");
        router.push("/applications");
      } else {
        setError(err instanceof Error ? err.message : "Could not create application");
      }
    } finally {
      setJobBusy(null);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Jobs</h1>
        <div className="flex flex-wrap gap-2">
          <button className="btn" disabled={globalBusy !== null}
            onClick={() => void runGlobal("Discover", () => api.discover())}>
            {globalBusy === "Discover" ? "Discovering…" : "Discover now"}
          </button>
          <button className="btn-secondary" disabled={globalBusy !== null}
            onClick={() => void runGlobal("Extract pending", () => api.extractPending())}>
            {globalBusy === "Extract pending" ? "Extracting…" : "Extract pending"}
          </button>
        </div>
      </div>
      {notice && <p className="text-sm text-emerald-400">{notice}</p>}
      {error && <p className="text-sm text-rose-400">{error}</p>}
      {jobs.length === 0 && (
        <p className="text-sm text-slate-400">
          No jobs yet — click “Discover now” to pull from the enabled sources.
        </p>
      )}

      <div className="space-y-4">
        {jobs.map((job) => (
          <article key={job.id} className="card">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="font-medium">{job.title ?? "(untitled)"}</h2>
              <span className={`badge ${STATUS_BADGE[job.status] ?? "bg-slate-700"}`}>{job.status}</span>
              <span className="badge bg-slate-800">{job.source}</span>
              <span className="ml-auto flex gap-2">
                {job.status === "discovered" && (
                  <button className="btn-secondary" disabled={jobBusy === job.id}
                    onClick={() => void extractOne(job)}>
                    {jobBusy === job.id ? "Extracting…" : "Extract"}
                  </button>
                )}
                <button className="btn" disabled={jobBusy === job.id} onClick={() => void apply(job)}>
                  {jobBusy === job.id ? "…" : "Apply (track)"}
                </button>
              </span>
            </div>
            <p className="mt-1 text-sm text-slate-400">
              {[job.company, job.location, job.employment_type.replace("_", " "), job.work_mode]
                .filter((part) => part && part !== "")
                .join(" · ")}
              {job.salary_max !== null && (
                <>
                  {" · "}{job.salary_min ?? "?"}–{job.salary_max} {job.currency ?? ""}
                </>
              )}
            </p>
            {(job.required_skills?.length ?? 0) > 0 && (
              <p className="mt-2 flex flex-wrap gap-1">
                {(job.required_skills ?? []).map((skill) => (
                  <span key={skill} className="badge bg-slate-800 text-slate-300">{skill}</span>
                ))}
              </p>
            )}
            {job.description && (
              <details className="mt-2">
                <summary className="cursor-pointer text-xs text-sky-400">Description</summary>
                <div className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap rounded bg-slate-950 p-3 text-xs text-slate-300">
                  {job.description}
                </div>
              </details>
            )}
            <p className="mt-2 text-xs text-slate-500">
              <a href={job.url} target="_blank" rel="noreferrer" className="hover:underline">
                {job.url}
              </a>
            </p>
          </article>
        ))}
      </div>
    </div>
  );
}