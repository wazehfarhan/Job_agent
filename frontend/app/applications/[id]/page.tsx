"use client";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useRequireAuth } from "@/lib/hooks";
import { APPLICATION_STATUSES, categoryBadge } from "../../applications/page";
import type { Application, StatusEvent } from "@/types/api";

export default function ApplicationDetailPage() {
  const ready = useRequireAuth();
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [application, setApplication] = useState<Application | null>(null);
  const [events, setEvents] = useState<StatusEvent[]>([]);
  const [status, setStatus] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const app = await api.getApplication(id);
      setApplication(app);
      setStatus(app.status);
      setEvents(await api.listEvents(id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load application");
    }
  }, [id]);

  useEffect(() => {
    if (ready && id) void load();
  }, [ready, id, load]);

  async function transition(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.transition(id, status, note.trim() === "" ? null : note.trim());
      setNote("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Transition failed");
    } finally {
      setBusy(false);
    }
  }

  if (!ready || !application) {
    return (
      <div className="space-y-3">
        <p className="text-slate-400">{error ?? "Loading…"}</p>
        <Link href="/applications" className="text-sm text-sky-400 hover:underline">← Back</Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-2">
        <h1 className="text-2xl font-semibold">Application</h1>
        <span className="badge bg-slate-700">{application.status.replace("_", " ")}</span>
        {application.match_category && (
          <span className={`badge ${categoryBadge(application.match_category)}`}>
            {application.match_category}
          </span>
        )}
        {application.match_score !== null && (
          <span className="text-lg font-medium">{application.match_score}/100</span>
        )}
        <Link href="/applications" className="ml-auto text-sm text-sky-400 hover:underline">
          ← All applications
        </Link>
      </div>

      {application.match_reasons.length > 0 && (
        <section className="card">
          <h2 className="font-medium">Why this score</h2>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-300">
            {application.match_reasons.map((reason, index) => (
              <li key={index}>{reason}</li>
            ))}
          </ul>
        </section>
      )}

      <section className="card space-y-3">
        <h2 className="font-medium">Change status</h2>
        {error && <p className="text-sm text-rose-400">{error}</p>}
        <form onSubmit={transition} className="grid gap-3 sm:grid-cols-[14rem_1fr_auto] sm:items-end">
          <div>
            <label className="label" htmlFor="status">New status</label>
            <select id="status" className="input" value={status} onChange={(e) => setStatus(e.target.value)}>
              {APPLICATION_STATUSES.map((value) => (
                <option key={value} value={value}>{value.replace("_", " ")}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label" htmlFor="note">Note (recorded on the timeline)</label>
            <input id="note" className="input" value={note} placeholder="e.g. applied via company site"
              onChange={(e) => setNote(e.target.value)} />
          </div>
          <button className="btn" disabled={busy || status === application.status}>
            {busy ? "Saving…" : "Transition"}
          </button>
        </form>
        <p className="text-xs text-slate-500">
          Every change appends to the timeline below — history is never rewritten.
        </p>
      </section>

      <section className="card">
        <h2 className="font-medium">Timeline</h2>
        <ol className="mt-3 space-y-3 border-l border-slate-800 pl-4">
          {events.map((event) => (
            <li key={event.id} className="relative">
              <span className="absolute -left-[1.32rem] top-1.5 h-2 w-2 rounded-full bg-sky-500" />
              <p className="text-sm font-medium">{event.status.replace("_", " ")}</p>
              {event.note && <p className="text-xs text-slate-400">{event.note}</p>}
              <p className="text-xs text-slate-600">{new Date(event.created_at).toLocaleString()}</p>
            </li>
          ))}
          {events.length === 0 && <li className="text-sm text-slate-400">No events yet.</li>}
        </ol>
      </section>

      <button className="btn-secondary" onClick={() => router.push("/applications")}>Back</button>
    </div>
  );
}