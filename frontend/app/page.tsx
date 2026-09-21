"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api, apiHealth } from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";
import type { Health } from "@/types/api";

const CARDS = [
  {
    href: "/jobs",
    title: "Jobs",
    body: "Discover postings from enabled sources, extract structured fields, and apply.",
  },
  {
    href: "/applications",
    title: "Applications",
    body: "Match scores with reasons, status transitions, and the full event timeline.",
  },
  {
    href: "/resumes",
    title: "Resumes",
    body: "Upload PDF/DOCX CVs, set a default, inspect the extracted text.",
  },
  {
    href: "/profile",
    title: "Profile",
    body: "Education, skills, experience, projects, and matching preferences.",
  },
];

export default function DashboardPage() {
  const [health, setHealth] = useState<Health | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);

  useEffect(() => {
    apiHealth()
      .then(setHealth)
      .catch((err: Error) => setHealthError(err.message));
  }, []);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="mt-1 text-sm text-slate-400">
          Discovery → extraction → matching runs server-side; this dashboard is your control room.
        </p>
      </header>

      <div className="card text-sm">
        {health ? (
          <p>
            Backend:{" "}
            <span className="font-medium text-emerald-400">online</span> · env{" "}
            <code className="text-slate-300">{health.env}</code>
          </p>
        ) : healthError ? (
          <p>
            Backend:{" "}
            <span className="font-medium text-rose-400">unreachable</span> ({healthError}) — is it
            running on port 8000?
          </p>
        ) : (
          <p className="text-slate-400">Checking backend…</p>
        )}
      </div>

      {!isLoggedIn() && (
        <div className="card text-sm">
          <p>
            You are not logged in.{" "}
            <Link href="/login" className="text-sky-400 hover:underline">
              Log in or register
            </Link>{" "}
            to use the agent.
          </p>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        {CARDS.map((card) => (
          <Link key={card.href} href={card.href} className="card block hover:border-sky-700">
            <h2 className="font-medium text-sky-300">{card.title}</h2>
            <p className="mt-1 text-sm text-slate-400">{card.body}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}