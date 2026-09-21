"use client";
import { useEffect, useState } from "react";
import { api, apiHealth } from "@/lib/api";
import { useRequireAuth } from "@/lib/hooks";
import type { Health, RuntimeSettings } from "@/types/api";

export default function SettingsPage() {
  const ready = useRequireAuth();
  const [settings, setSettings] = useState<RuntimeSettings | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ready) return;
    api
      .getSettings()
      .then(setSettings)
      .catch((err: Error) => setError(err.message));
    apiHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, [ready]);

  if (!ready) return <p className="text-slate-400">Loading…</p>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Settings</h1>
      {error && <p className="text-sm text-rose-400">{error}</p>}

      <section className="card">
        <h2 className="font-medium">Backend status</h2>
        <p className="mt-1 text-sm text-slate-300">
          {health ? (
            <>
              <span className="text-emerald-400">online</span> · env {health.env}
            </>
          ) : (
            <span className="text-rose-400">unreachable</span>
          )}
        </p>
      </section>

      <section className="card">
        <h2 className="font-medium">Runtime configuration (read-only)</h2>
        <p className="mt-1 text-xs text-slate-500">
          These values come from the backend&apos;s <code>.env</code> file — edit it and restart the
          backend to change them. Secrets (API keys, connection URLs) are never exposed here.
        </p>
        {settings && (
          <dl className="mt-3 grid gap-x-6 gap-y-2 text-sm sm:grid-cols-[14rem_1fr]">
            <dt className="text-slate-400">Environment</dt>
            <dd>{settings.env}</dd>
            <dt className="text-slate-400">AI provider</dt>
            <dd>{settings.ai_provider}</dd>
            <dt className="text-slate-400">AI model (completion)</dt>
            <dd>{settings.ai_model}</dd>
            <dt className="text-slate-400">AI model (embeddings)</dt>
            <dd>{settings.ai_embed_model}</dd>
            <dt className="text-slate-400">Job source config</dt>
            <dd><code className="text-slate-300">{settings.job_source_config}</code></dd>
            <dt className="text-slate-400">Max upload size</dt>
            <dd>{settings.max_upload_mb} MB</dd>
            <dt className="text-slate-400">Browser headless</dt>
            <dd>{String(settings.browser_headless)}</dd>
          </dl>
        )}
      </section>

      <section className="card text-sm text-slate-300">
        <h2 className="font-medium">Enabling sources</h2>
        <p className="mt-1">
          <code>JOB_SOURCE_CONFIG</code> is a JSON map of source name → bool.{" "}
          <code>{"{}"}</code> enables every registered source; e.g.{" "}
          <code>{'{"remotive": true}'}</code> enables only Remotive. Registered adapters live in{" "}
          <code>backend/app/sources/</code>.
        </p>
      </section>
    </div>
  );
}