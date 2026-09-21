"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useRequireAuth } from "@/lib/hooks";
import type { Application } from "@/types/api";

export const APPLICATION_STATUSES = [
  "discovered", "analyzing", "matched", "preparing", "awaiting_approval",
  "approved", "submitting", "applied", "interview", "rejected",
  "withdrawn", "failed", "needs_user_action",
] as const;

export function categoryBadge(category: string | null): string {
  switch (category) {
    case "strong":
      return "bg-emerald-700";
    case "possible":
      return "bg-amber-700";
    case "weak":
      return "bg-orange-800";
    case "ineligible":
      return "bg-rose-800";
    default:
      return "bg-slate-700";
  }
}

export default function ApplicationsPage() {
  const ready = useRequireAuth();
  const [applications, setApplications] = useState<Application[]>([]);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setApplications(await api.listApplications());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load applications");
    }
  }, []);

  useEffect(() => {
    if (ready) void load();
  }, [ready, load]);

  async function match(id: string) {
    setBusyId(id);
    setError(null);
    try {
      await api.matchApplication(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Match failed");
    } finally {
      setBusyId(null);
    }
  }

  async function transition(id: string, status: string) {
    setBusyId(id);
    setError(null);
    try {
      await api.transition(id, status, null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Transition failed");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Applications</h1>
      {error && <p className="text-sm text-rose-400">{error}</p>}
      {applications.length === 0 && (
        <p className="text-sm text-slate-400">
          No applications yet — open <Link href="/jobs" className="text-sky-400 hover:underline">Jobs</Link>{" "}
          and click “Apply (track)” on a posting.
        </p>
      )}

      <div className="space-y-3">
        {applications.map((application) => (
          <div key={application.id} className="card">
            <div className="flex flex-wrap items-center gap-2">
              <Link href={`/applications/${application.id}`} className="font-medium text-sky-300 hover:underline">
                Application
              </Link>
              <span className="badge bg-slate-700">{application.status.replace("_", " ")}</span>
              {application.match_category && (
                <span className={`badge ${categoryBadge(application.match_category)}`}>
                  {application.match_category}
                </span>
              )}
              {application.match_score !== null && (
                <span className="text-sm font-medium">{application.match_score}/100</span>
              )}
              <span className="ml-auto flex gap-2">
                <button className="btn-secondary" disabled={busyId === application.id}
                  onClick={() => void match(application.id)}>
                  {busyId === application.id ? "Matching…" : "Match"}
                </button>
                <select
                  className="input w-44"
                  value={application.status}
                  disabled={busyId === application.id}
                  onChange={(e) => void transition(application.id, e.target.value)}
                >
                  {APPLICATION_STATUSES.map((status) => (
                    <option key={status} value={status}>{status.replace("_", " ")}</option>
                  ))}
                </select>
              </span>
            </div>
            {application.match_reasons.length > 0 && (
              <ul className="mt-2 list-disc space-y-0.5 pl-5 text-xs text-slate-400">
                {application.match_reasons.map((reason, index) => (
                  <li key={index}>{reason}</li>
                ))}
              </ul>
            )}
            <p className="mt-2 text-xs text-slate-500">
              created {new Date(application.created_at).toLocaleString()} ·{" "}
              <Link href={`/applications/${application.id}`} className="text-sky-400 hover:underline">
                timeline →
              </Link>
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}