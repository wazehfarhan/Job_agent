"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useRequireAuth } from "@/lib/hooks";
import type { ProfileOut } from "@/types/api";

// --- local form row types (everything is a string; converted on save) ------

type EduRow = {
  institution: string;
  degree: string;
  field: string;
  start_date: string;
  expected_graduation: string;
  gpa: string;
};
type CertRow = { name: string; issuer: string; date: string; credential_url: string };
type SkillRow = { category: string; name: string };
type ExpRow = {
  organization: string;
  position: string;
  start_date: string;
  end_date: string;
  description: string;
  skills_used_csv: string;
  achievements_csv: string;
};
type ProjRow = {
  name: string;
  description: string;
  technologies_csv: string;
  url: string;
  github_url: string;
  responsibilities_csv: string;
  achievements_csv: string;
};
type PrefsForm = {
  target_roles_csv: string;
  job_types_csv: string;
  internship_types_csv: string;
  preferred_locations_csv: string;
  work_modes_csv: string;
  min_salary: string;
  min_stipend: string;
  preferred_industries_csv: string;
  keywords_csv: string;
  excluded_companies_csv: string;
  excluded_roles_csv: string;
  min_match_score: string;
};
type FormState = {
  full_name: string;
  phone: string;
  country: string;
  city: string;
  portfolio_url: string;
  github_url: string;
  linkedin_url: string;
  other_links_csv: string;
  educations: EduRow[];
  certifications: CertRow[];
  skills: SkillRow[];
  experiences: ExpRow[];
  projects: ProjRow[];
  prefs: PrefsForm;
};

const SKILL_CATEGORIES = [
  "programming_language", "framework", "library", "database", "cloud",
  "ai_ml", "nlp", "devops", "testing", "other",
];

const EMPTY_EDU: EduRow = { institution: "", degree: "", field: "", start_date: "", expected_graduation: "", gpa: "" };
const EMPTY_CERT: CertRow = { name: "", issuer: "", date: "", credential_url: "" };
const EMPTY_SKILL: SkillRow = { category: "other", name: "" };
const EMPTY_EXP: ExpRow = { organization: "", position: "", start_date: "", end_date: "", description: "", skills_used_csv: "", achievements_csv: "" };
const EMPTY_PROJ: ProjRow = { name: "", description: "", technologies_csv: "", url: "", github_url: "", responsibilities_csv: "", achievements_csv: "" };
const EMPTY_PREFS: PrefsForm = {
  target_roles_csv: "", job_types_csv: "", internship_types_csv: "", preferred_locations_csv: "",
  work_modes_csv: "", min_salary: "", min_stipend: "", preferred_industries_csv: "",
  keywords_csv: "", excluded_companies_csv: "", excluded_roles_csv: "", min_match_score: "",
};

// --- conversion helpers (form strings ⇄ API nulls/numbers/lists) ------------

const orNull = (s: string) => (s.trim() === "" ? null : s.trim());
const numOrNull = (s: string) => (s.trim() === "" ? null : Number(s));
const splitList = (csv: string) => csv.split(",").map((item) => item.trim()).filter((item) => item !== "");

function toForm(profile: ProfileOut): FormState {
  const prefs = profile.preferences;
  const num = (v: number | null) => (v === null ? "" : String(v));
  const join = (list: string[] | null | undefined) => (list ?? []).join(", ");
  return {
    full_name: profile.full_name ?? "",
    phone: profile.phone ?? "",
    country: profile.country ?? "",
    city: profile.city ?? "",
    portfolio_url: profile.portfolio_url ?? "",
    github_url: profile.github_url ?? "",
    linkedin_url: profile.linkedin_url ?? "",
    other_links_csv: join(profile.other_links),
    educations: profile.educations.map((e) => ({
      institution: e.institution ?? "", degree: e.degree ?? "", field: e.field ?? "",
      start_date: e.start_date ?? "", expected_graduation: e.expected_graduation ?? "",
      gpa: e.gpa === null ? "" : String(e.gpa),
    })),
    certifications: profile.certifications.map((c) => ({
      name: c.name ?? "", issuer: c.issuer ?? "", date: c.date ?? "", credential_url: c.credential_url ?? "",
    })),
    skills: profile.skills.map((s) => ({ category: s.category, name: s.name })),
    experiences: profile.experiences.map((x) => ({
      organization: x.organization ?? "", position: x.position ?? "", start_date: x.start_date ?? "",
      end_date: x.end_date ?? "", description: x.description ?? "",
      skills_used_csv: join(x.skills_used), achievements_csv: join(x.achievements),
    })),
    projects: profile.projects.map((p) => ({
      name: p.name ?? "", description: p.description ?? "", technologies_csv: join(p.technologies),
      url: p.url ?? "", github_url: p.github_url ?? "",
      responsibilities_csv: join(p.responsibilities), achievements_csv: join(p.achievements),
    })),
    prefs: {
      target_roles_csv: join(prefs?.target_roles), job_types_csv: join(prefs?.job_types),
      internship_types_csv: join(prefs?.internship_types), preferred_locations_csv: join(prefs?.preferred_locations),
      work_modes_csv: join(prefs?.work_modes), min_salary: num(prefs?.min_salary ?? null),
      min_stipend: num(prefs?.min_stipend ?? null), preferred_industries_csv: join(prefs?.preferred_industries),
      keywords_csv: join(prefs?.keywords), excluded_companies_csv: join(prefs?.excluded_companies),
      excluded_roles_csv: join(prefs?.excluded_roles), min_match_score: num(prefs?.min_match_score ?? null),
    },
  };
}

function TextField(props: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="label">{props.label}</label>
      <input
        className="input"
        type={props.type ?? "text"}
        value={props.value}
        placeholder={props.placeholder}
        onChange={(e) => props.onChange(e.target.value)}
      />
    </div>
  );
}


function updateRow<T>(list: T[], index: number, patch: Partial<T>): T[] {
  return list.map((row, i) => (i === index ? { ...row, ...patch } : row));
}

export default function ProfilePage() {
  const ready = useRequireAuth();
  const [form, setForm] = useState<FormState | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setForm(toForm(await api.getProfile()));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load profile");
    }
  }, []);

  useEffect(() => {
    if (ready) void load();
  }, [ready, load]);

  if (!ready || !form) {
    return <p className="text-slate-400">{error ?? "Loading…"}</p>;
  }

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((prev) => (prev ? { ...prev, [key]: value } : prev));

  const setPrefs = (key: keyof PrefsForm, value: string) =>
    setForm((prev) => (prev ? { ...prev, prefs: { ...prev.prefs, [key]: value } } : prev));

  async function save() {
    setBusy(true);
    setError(null);
    setStatus(null);
    try {
      const payload: ProfileOut = {
        id: "", // ignored by PUT /profile/me
        full_name: orNull(form.full_name),
        phone: orNull(form.phone),
        country: orNull(form.country),
        city: orNull(form.city),
        portfolio_url: orNull(form.portfolio_url),
        github_url: orNull(form.github_url),
        linkedin_url: orNull(form.linkedin_url),
        other_links: splitList(form.other_links_csv),
        educations: form.educations.map((e) => ({
          institution: orNull(e.institution), degree: orNull(e.degree), field: orNull(e.field),
          start_date: orNull(e.start_date), expected_graduation: orNull(e.expected_graduation),
          gpa: numOrNull(e.gpa),
        })),
        certifications: form.certifications.map((c) => ({
          name: orNull(c.name), issuer: orNull(c.issuer), date: orNull(c.date),
          credential_url: orNull(c.credential_url),
        })),
        skills: form.skills.filter((s) => s.name.trim() !== ""),
        experiences: form.experiences.map((x) => ({
          organization: orNull(x.organization), position: orNull(x.position),
          start_date: orNull(x.start_date), end_date: orNull(x.end_date),
          description: orNull(x.description), skills_used: splitList(x.skills_used_csv),
          achievements: splitList(x.achievements_csv),
        })),
        projects: form.projects.map((p) => ({
          name: orNull(p.name), description: orNull(p.description),
          technologies: splitList(p.technologies_csv), url: orNull(p.url),
          github_url: orNull(p.github_url), responsibilities: splitList(p.responsibilities_csv),
          achievements: splitList(p.achievements_csv),
        })),
        preferences: {
          target_roles: splitList(form.prefs.target_roles_csv),
          job_types: splitList(form.prefs.job_types_csv),
          internship_types: splitList(form.prefs.internship_types_csv),
          preferred_locations: splitList(form.prefs.preferred_locations_csv),
          work_modes: splitList(form.prefs.work_modes_csv),
          min_salary: numOrNull(form.prefs.min_salary),
          min_stipend: numOrNull(form.prefs.min_stipend),
          preferred_industries: splitList(form.prefs.preferred_industries_csv),
          keywords: splitList(form.prefs.keywords_csv),
          excluded_companies: splitList(form.prefs.excluded_companies_csv),
          excluded_roles: splitList(form.prefs.excluded_roles_csv),
          min_match_score: numOrNull(form.prefs.min_match_score),
        },
      };
      await api.updateProfile(payload);
      setStatus("Profile saved.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setBusy(false);
    }
  }


  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Profile</h1>
        <button className="btn" onClick={() => void save()} disabled={busy}>
          {busy ? "Saving…" : "Save profile"}
        </button>
      </div>
      {status && <p className="text-sm text-emerald-400">{status}</p>}
      {error && <p className="text-sm text-rose-400">{error}</p>}

      <section className="card space-y-3">
        <h2 className="font-medium">Personal</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <TextField label="Full name" value={form.full_name} onChange={(v) => set("full_name", v)} />
          <TextField label="Phone" value={form.phone} onChange={(v) => set("phone", v)} />
          <TextField label="Country" value={form.country} onChange={(v) => set("country", v)} />
          <TextField label="City" value={form.city} onChange={(v) => set("city", v)} />
          <TextField label="Portfolio URL" value={form.portfolio_url} onChange={(v) => set("portfolio_url", v)} />
          <TextField label="GitHub URL" value={form.github_url} onChange={(v) => set("github_url", v)} />
          <TextField label="LinkedIn URL" value={form.linkedin_url} onChange={(v) => set("linkedin_url", v)} />
          <TextField label="Other links (comma-separated)" value={form.other_links_csv} onChange={(v) => set("other_links_csv", v)} />
        </div>
      </section>

      <section className="card space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="font-medium">Education</h2>
          <button className="btn-secondary" onClick={() => set("educations", [...form.educations, { ...EMPTY_EDU }])}>
            Add education
          </button>
        </div>
        {form.educations.length === 0 && <p className="text-sm text-slate-500">None added.</p>}
        {form.educations.map((edu, index) => (
          <div key={index} className="rounded border border-slate-800 p-3">
            <div className="grid gap-3 sm:grid-cols-3">
              <TextField label="Institution" value={edu.institution}
                onChange={(v) => set("educations", updateRow(form.educations, index, { institution: v }))} />
              <TextField label="Degree" value={edu.degree}
                onChange={(v) => set("educations", updateRow(form.educations, index, { degree: v }))} />
              <TextField label="Field" value={edu.field}
                onChange={(v) => set("educations", updateRow(form.educations, index, { field: v }))} />
              <TextField label="Start date" value={edu.start_date}
                onChange={(v) => set("educations", updateRow(form.educations, index, { start_date: v }))} />
              <TextField label="Expected graduation" value={edu.expected_graduation}
                onChange={(v) => set("educations", updateRow(form.educations, index, { expected_graduation: v }))} />
              <TextField label="GPA (optional)" value={edu.gpa}
                onChange={(v) => set("educations", updateRow(form.educations, index, { gpa: v }))} />
            </div>
            <button className="btn-danger mt-2"
              onClick={() => set("educations", form.educations.filter((_, i) => i !== index))}>
              Remove
            </button>
          </div>
        ))}
      </section>


      <section className="card space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="font-medium">Certifications</h2>
          <button className="btn-secondary" onClick={() => set("certifications", [...form.certifications, { ...EMPTY_CERT }])}>
            Add certification
          </button>
        </div>
        {form.certifications.length === 0 && <p className="text-sm text-slate-500">None added.</p>}
        {form.certifications.map((cert, index) => (
          <div key={index} className="rounded border border-slate-800 p-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <TextField label="Name" value={cert.name}
                onChange={(v) => set("certifications", updateRow(form.certifications, index, { name: v }))} />
              <TextField label="Issuer" value={cert.issuer}
                onChange={(v) => set("certifications", updateRow(form.certifications, index, { issuer: v }))} />
              <TextField label="Date" value={cert.date}
                onChange={(v) => set("certifications", updateRow(form.certifications, index, { date: v }))} />
              <TextField label="Credential URL" value={cert.credential_url}
                onChange={(v) => set("certifications", updateRow(form.certifications, index, { credential_url: v }))} />
            </div>
            <button className="btn-danger mt-2"
              onClick={() => set("certifications", form.certifications.filter((_, i) => i !== index))}>
              Remove
            </button>
          </div>
        ))}
      </section>

      <section className="card space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="font-medium">Skills</h2>
          <button className="btn-secondary" onClick={() => set("skills", [...form.skills, { ...EMPTY_SKILL }])}>
            Add skill
          </button>
        </div>
        {form.skills.length === 0 && <p className="text-sm text-slate-500">None added.</p>}
        {form.skills.map((skill, index) => (
          <div key={index} className="flex items-end gap-2">
            <div className="w-48">
              <label className="label">Category</label>
              <select className="input" value={skill.category}
                onChange={(e) => set("skills", updateRow(form.skills, index, { category: e.target.value }))}>
                {SKILL_CATEGORIES.map((category) => (
                  <option key={category} value={category}>{category.replace("_", " ")}</option>
                ))}
              </select>
            </div>
            <div className="flex-1">
              <TextField label="Name" value={skill.name}
                onChange={(v) => set("skills", updateRow(form.skills, index, { name: v }))} />
            </div>
            <button className="btn-danger" onClick={() => set("skills", form.skills.filter((_, i) => i !== index))}>
              Remove
            </button>
          </div>
        ))}
      </section>

      <section className="card space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="font-medium">Experience</h2>
          <button className="btn-secondary" onClick={() => set("experiences", [...form.experiences, { ...EMPTY_EXP }])}>
            Add experience
          </button>
        </div>
        {form.experiences.length === 0 && <p className="text-sm text-slate-500">None added.</p>}
        {form.experiences.map((exp, index) => (
          <div key={index} className="rounded border border-slate-800 p-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <TextField label="Organization" value={exp.organization}
                onChange={(v) => set("experiences", updateRow(form.experiences, index, { organization: v }))} />
              <TextField label="Position" value={exp.position}
                onChange={(v) => set("experiences", updateRow(form.experiences, index, { position: v }))} />
              <TextField label="Start date" value={exp.start_date}
                onChange={(v) => set("experiences", updateRow(form.experiences, index, { start_date: v }))} />
              <TextField label="End date (empty = ongoing)" value={exp.end_date}
                onChange={(v) => set("experiences", updateRow(form.experiences, index, { end_date: v }))} />
            </div>
            <div className="mt-3">
              <label className="label">Description</label>
              <textarea className="input" rows={2} value={exp.description}
                onChange={(e) => set("experiences", updateRow(form.experiences, index, { description: e.target.value }))} />
            </div>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <TextField label="Skills used (comma-separated)" value={exp.skills_used_csv}
                onChange={(v) => set("experiences", updateRow(form.experiences, index, { skills_used_csv: v }))} />
              <TextField label="Achievements (comma-separated)" value={exp.achievements_csv}
                onChange={(v) => set("experiences", updateRow(form.experiences, index, { achievements_csv: v }))} />
            </div>
            <button className="btn-danger mt-2"
              onClick={() => set("experiences", form.experiences.filter((_, i) => i !== index))}>
              Remove
            </button>
          </div>
        ))}
      </section>


      <section className="card space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="font-medium">Projects</h2>
          <button className="btn-secondary" onClick={() => set("projects", [...form.projects, { ...EMPTY_PROJ }])}>
            Add project
          </button>
        </div>
        {form.projects.length === 0 && <p className="text-sm text-slate-500">None added.</p>}
        {form.projects.map((project, index) => (
          <div key={index} className="rounded border border-slate-800 p-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <TextField label="Name" value={project.name}
                onChange={(v) => set("projects", updateRow(form.projects, index, { name: v }))} />
              <TextField label="Live URL" value={project.url}
                onChange={(v) => set("projects", updateRow(form.projects, index, { url: v }))} />
              <TextField label="GitHub URL" value={project.github_url}
                onChange={(v) => set("projects", updateRow(form.projects, index, { github_url: v }))} />
              <TextField label="Technologies (comma-separated)" value={project.technologies_csv}
                onChange={(v) => set("projects", updateRow(form.projects, index, { technologies_csv: v }))} />
            </div>
            <div className="mt-3">
              <label className="label">Description</label>
              <textarea className="input" rows={2} value={project.description}
                onChange={(e) => set("projects", updateRow(form.projects, index, { description: e.target.value }))} />
            </div>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <TextField label="Responsibilities (comma-separated)" value={project.responsibilities_csv}
                onChange={(v) => set("projects", updateRow(form.projects, index, { responsibilities_csv: v }))} />
              <TextField label="Achievements (comma-separated)" value={project.achievements_csv}
                onChange={(v) => set("projects", updateRow(form.projects, index, { achievements_csv: v }))} />
            </div>
            <button className="btn-danger mt-2"
              onClick={() => set("projects", form.projects.filter((_, i) => i !== index))}>
              Remove
            </button>
          </div>
        ))}
      </section>

      <section className="card space-y-3">
        <h2 className="font-medium">Matching preferences</h2>
        <p className="text-xs text-slate-500">
          Consumed by the Matching Agent: hard filters (work modes, job types, salary floor,
          exclusions) run before scoring; everything else informs the ranking.
        </p>
        <div className="grid gap-3 sm:grid-cols-2">
          <TextField label="Target roles (comma-separated)" value={prefs.target_roles_csv}
            onChange={(v) => setPrefs("target_roles_csv", v)} />
          <TextField label="Preferred locations (comma-separated)" value={prefs.preferred_locations_csv}
            onChange={(v) => setPrefs("preferred_locations_csv", v)} />
          <TextField label="Job types (e.g. internship, full_time)" value={prefs.job_types_csv}
            onChange={(v) => setPrefs("job_types_csv", v)} />
          <TextField label="Internship types" value={prefs.internship_types_csv}
            onChange={(v) => setPrefs("internship_types_csv", v)} />
          <TextField label="Work modes (remote, hybrid, onsite)" value={prefs.work_modes_csv}
            onChange={(v) => setPrefs("work_modes_csv", v)} />
          <TextField label="Preferred industries (comma-separated)" value={prefs.preferred_industries_csv}
            onChange={(v) => setPrefs("preferred_industries_csv", v)} />
          <TextField label="Keywords" value={prefs.keywords_csv}
            onChange={(v) => setPrefs("keywords_csv", v)} />
          <TextField label="Excluded companies (comma-separated)" value={prefs.excluded_companies_csv}
            onChange={(v) => setPrefs("excluded_companies_csv", v)} />
          <TextField label="Excluded roles (comma-separated)" value={prefs.excluded_roles_csv}
            onChange={(v) => setPrefs("excluded_roles_csv", v)} />
          <TextField label="Minimum salary" value={prefs.min_salary} type="number"
            onChange={(v) => setPrefs("min_salary", v)} />
          <TextField label="Minimum stipend" value={prefs.min_stipend} type="number"
            onChange={(v) => setPrefs("min_stipend", v)} />
          <TextField label="Minimum match score (0–100)" value={prefs.min_match_score} type="number"
            onChange={(v) => setPrefs("min_match_score", v)} />
        </div>
      </section>
    </div>
  );
}