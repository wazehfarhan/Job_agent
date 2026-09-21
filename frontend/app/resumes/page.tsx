"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useRequireAuth } from "@/lib/hooks";
import type { Resume, ResumeDetail } from "@/types/api";

export default function ResumesPage() {
  const ready = useRequireAuth();
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [label, setLabel] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setResumes(await api.listResumes());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load resumes");
    }
  }, []);

  useEffect(() => {
    if (ready) void load();
  }, [ready, load]);

  async function upload(event: React.FormEvent) {
    event.preventDefault();
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      await api.uploadResume(label.trim() || "Untitled", file);
      setLabel("");
      setFile(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function makeDefault(id: string) {
    setError(null);
    try {
      await api.setDefaultResume(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not set default");
    }
  }

  async function remove(id: string) {
    setError(null);
    try {
      await api.deleteResume(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Resumes</h1>

      <form onSubmit={upload} className="card space-y-3">
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <label className="label" htmlFor="label">Label</label>
            <input id="label" className="input" value={label} placeholder="e.g. AI/ML Resume"
              onChange={(e) => setLabel(e.target.value)} />
          </div>
          <div>
            <label className="label" htmlFor="file">File (PDF or DOCX)</label>
            <input id="file" type="file" accept=".pdf,.docx" required
              className="input file:mr-3 file:rounded file:border-0 file:bg-slate-700 file:px-2 file:py-1 file:text-slate-200"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          </div>
        </div>
        {error && <p className="text-sm text-rose-400">{error}</p>}
        <button className="btn" disabled={busy || !file}>
          {busy ? "Uploading…" : "Upload resume"}
        </button>
      </form>

      <div className="space-y-3">
        {resumes.length === 0 && (
          <p className="text-sm text-slate-400">No resumes yet — upload your first CV above.</p>
        )}
        {resumes.map((resume) => (
          <div key={resume.id} className="card">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-medium">{resume.label}</span>
              {resume.is_default && <span className="badge bg-emerald-700">default</span>}
              <span className="badge bg-slate-700 uppercase">{resume.file_type}</span>
              <span className="text-xs text-slate-500">{resume.original_filename}</span>
              <span className="ml-auto flex gap-2">
                {!resume.is_default && (
                  <button className="btn-secondary" onClick={() => void makeDefault(resume.id)}>
                    Set default
                  </button>
                )}
                <button className="btn-danger" onClick={() => void remove(resume.id)}>
                  Delete
                </button>
              </span>
            </div>
            <ResumeText id={resume.id} />
          </div>
        ))}
      </div>
    </div>
  );
}

function ResumeText({ id }: { id: string }) {
  const [detail, setDetail] = useState<ResumeDetail | null>(null);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function toggle() {
    if (open) {
      setOpen(false);
      return;
    }
    if (!detail) {
      try {
        setDetail(await api.getResume(id));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load parsed text");
      }
    }
    setOpen(true);
  }

  return (
    <div className="mt-2">
      <button className="text-xs text-sky-400 hover:underline" onClick={() => void toggle()}>
        {open ? "Hide parsed text" : "Show parsed text"}
      </button>
      {error && <span className="ml-2 text-xs text-rose-400">{error}</span>}
      {open && detail && (
        <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap rounded bg-slate-950 p-3 text-xs text-slate-300">
          {detail.parsed_text ?? "(no text extracted — scanned/image-only PDF?)"}
        </pre>
      )}
    </div>
  );
}