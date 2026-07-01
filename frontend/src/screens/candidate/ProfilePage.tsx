"use client";

import {
  UserRound, Pencil, Save, X, Loader2, CheckCircle2, AlertCircle,
  Mail, Phone, MapPin, Briefcase, GraduationCap, Link2,
  Building2, Calendar, Clock, DollarSign, Plus, Trash2,
  Linkedin, Github, Globe, ChevronRight, Star, Sparkles
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { apiClient } from "../../api/client";

type WorkEntry = { role: string; company: string; duration: string };
type EduEntry  = { institution: string; degree: string; field: string; year_start: string; year_end: string };
type Profile = {
  candidate_id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  phone: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  current_company: string | null;
  current_role: string | null;
  total_experience: number | null;
  expected_salary: number | null;
  notice_period: string | null;
  highest_education: string | null;
  linkedin_url: string | null;
  github_url: string | null;
  portfolio_url: string | null;
  skills: string[];
  work_history: WorkEntry[];
  education_history: EduEntry[];
  profile_completion_percentage: number;
  source_type: string;
  verification_status: string;
  talent_pool_status: string;
  profile_freshness_status: string;
  member_since: string | null;
  profile_last_refreshed_at: string | null;
};

type SectionId = "personal" | "professional" | "skills" | "links" | "work" | "education" | null;

function fmt(d: string | null) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

/* ── Completion Ring ──────────────────────────────────────── */
function CompletionRing({ pct }: { pct: number }) {
  const r    = 42;
  const circ = 2 * Math.PI * r;
  const dash = circ * (pct / 100);
  const color = pct >= 80 ? "#10b981" : pct >= 50 ? "#f59e0b" : "#ef4444";
  const trackColor = pct >= 80 ? "#d1fae5" : pct >= 50 ? "#fef3c7" : "#fee2e2";
  return (
    <div className="relative flex h-28 w-28 items-center justify-center">
      <svg className="-rotate-90" width="112" height="112" viewBox="0 0 112 112">
        <circle cx="56" cy="56" r={r} fill="none" stroke={trackColor} strokeWidth="8" />
        <circle cx="56" cy="56" r={r} fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
          style={{ transition: "stroke-dasharray 0.7s cubic-bezier(.4,0,.2,1)" }} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center gap-0.5">
        <span className="text-2xl font-extrabold text-slate-900 leading-none">{pct}%</span>
        <span className="text-2xs font-semibold text-slate-400 uppercase tracking-widest">complete</span>
      </div>
    </div>
  );
}

/* ── Skills Tag Editor ─────────────────────────────────────── */
function SkillsEditor({ value, onChange }: { value: string[]; onChange: (v: string[]) => void }) {
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  function add() {
    const t = input.trim();
    if (t && !value.includes(t)) onChange([...value, t]);
    setInput("");
  }
  function onKey(e: React.KeyboardEvent) {
    if (e.key === "Enter" || e.key === ",") { e.preventDefault(); add(); }
    if (e.key === "Backspace" && !input && value.length) onChange(value.slice(0, -1));
  }

  return (
    <div className="flex min-h-[48px] flex-wrap gap-2 cursor-text rounded-[10px] border border-slate-200 bg-white px-3.5 py-2.5 shadow-sm focus-within:border-brand-400 focus-within:ring-[3px] focus-within:ring-brand-500/15 transition-all"
      onClick={() => inputRef.current?.focus()}>
      {value.map(s => (
        <span key={s} className="inline-flex items-center gap-1 rounded-full bg-brand-50 border border-brand-200 px-3 py-1 text-xs font-semibold text-brand-700">
          {s}
          <button type="button" onClick={() => onChange(value.filter(v => v !== s))} className="text-brand-400 hover:text-brand-700 transition">
            <X className="h-3 w-3" />
          </button>
        </span>
      ))}
      <input ref={inputRef} value={input} onChange={e => setInput(e.target.value)} onKeyDown={onKey} onBlur={add}
        className="min-w-[160px] flex-1 border-0 bg-transparent text-sm text-slate-900 placeholder:text-slate-400 outline-none"
        placeholder={value.length === 0 ? "Type a skill, press Enter or comma…" : "Add more…"} />
    </div>
  );
}

/* ── Field ──────────────────────────────────────────────── */
function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label className="block text-xs font-bold text-slate-600 uppercase tracking-wide">{label}</label>
      {children}
      {hint && <p className="text-2xs text-slate-400">{hint}</p>}
    </div>
  );
}

/* ── Detail Row ──────────────────────────────────────────── */
function DetailRow({ icon: Icon, label, value, href }: { icon: React.ElementType; label: string; value?: string | null; href?: string }) {
  if (!value) return null;
  return (
    <div className="flex items-start gap-3 py-2.5 border-b border-slate-50 last:border-0">
      <div className="mt-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-xl bg-slate-100">
        <Icon className="h-4 w-4 text-slate-500" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-2xs font-bold uppercase tracking-widest text-slate-400">{label}</p>
        {href ? (
          <a href={href} target="_blank" rel="noopener noreferrer"
            className="text-sm font-medium text-brand-600 hover:underline truncate block">{value}</a>
        ) : (
          <p className="text-sm font-medium text-slate-800 break-words">{value}</p>
        )}
      </div>
    </div>
  );
}

/* ── Section Card ─────────────────────────────────────────── */
function Section({
  title, icon: Icon, children, editId, activeEdit, onEdit, onSave, onCancel, saving,
}: {
  title: string;
  icon: React.ElementType;
  children: React.ReactNode;
  editId: SectionId;
  activeEdit: SectionId;
  onEdit: () => void;
  onSave: () => void;
  onCancel: () => void;
  saving: boolean;
}) {
  const isEditing = activeEdit === editId;
  return (
    <div className="card overflow-hidden">
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
        <div className="flex items-center gap-2.5">
          <Icon className="h-4 w-4 text-brand-600" />
          <h2 className="text-sm font-bold text-slate-800">{title}</h2>
        </div>
        {!isEditing ? (
          <button onClick={onEdit} disabled={activeEdit !== null && !isEditing}
            className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-500 hover:bg-slate-100 hover:text-slate-800 transition disabled:opacity-40">
            <Pencil className="h-3.5 w-3.5" /> Edit
          </button>
        ) : (
          <div className="flex items-center gap-2">
            <button onClick={onCancel} className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-500 hover:bg-slate-100 transition">
              <X className="h-3.5 w-3.5" /> Cancel
            </button>
            <button onClick={onSave} disabled={saving}
              className="flex items-center gap-1.5 rounded-lg bg-brand-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-brand-700 transition disabled:opacity-60">
              {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
              Save
            </button>
          </div>
        )}
      </div>
      <div className="px-6 py-5">{children}</div>
    </div>
  );
}

/* ── Work History Entry Editor ──────────────────────────── */
function WorkEntryEditor({ entries, onChange }: { entries: WorkEntry[]; onChange: (v: WorkEntry[]) => void }) {
  function update(i: number, field: keyof WorkEntry, val: string) {
    const next = entries.map((e, idx) => idx === i ? { ...e, [field]: val } : e);
    onChange(next);
  }
  function remove(i: number) { onChange(entries.filter((_, idx) => idx !== i)); }
  function addEntry() { onChange([{ role: "", company: "", duration: "" }, ...entries]); }

  return (
    <div className="space-y-4">
      <button onClick={addEntry} className="flex items-center gap-1.5 text-sm font-semibold text-brand-600 hover:text-brand-800 transition">
        <Plus className="h-4 w-4" /> Add Work Experience
      </button>
      {entries.map((entry, i) => (
        <div key={i} className="relative rounded-xl border border-slate-200 bg-slate-50 p-4 space-y-3">
          <button onClick={() => remove(i)}
            className="absolute right-3 top-3 flex items-center justify-center rounded-lg p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-500 transition">
            <Trash2 className="h-3.5 w-3.5" />
          </button>
          <div className="grid gap-3 sm:grid-cols-2 pr-8">
            <Field label="Role / Title">
              <input className="input" placeholder="e.g. Senior Software Engineer"
                value={entry.role} onChange={e => update(i, "role", e.target.value)} />
            </Field>
            <Field label="Company">
              <input className="input" placeholder="e.g. Infosys"
                value={entry.company} onChange={e => update(i, "company", e.target.value)} />
            </Field>
          </div>
          <Field label="Duration">
            <input className="input" placeholder="e.g. Jan 2021 – Mar 2023 · 2 yrs 2 mos"
              value={entry.duration} onChange={e => update(i, "duration", e.target.value)} />
          </Field>
        </div>
      ))}
      {entries.length === 0 && (
        <p className="text-sm text-slate-400 text-center py-4">No work experience added yet.</p>
      )}
    </div>
  );
}

/* ── Education Entry Editor ─────────────────────────────── */
function EducationEntryEditor({ entries, onChange }: { entries: EduEntry[]; onChange: (v: EduEntry[]) => void }) {
  function update(i: number, field: keyof EduEntry, val: string) {
    onChange(entries.map((e, idx) => idx === i ? { ...e, [field]: val } : e));
  }
  function remove(i: number) { onChange(entries.filter((_, idx) => idx !== i)); }
  function addEntry() {
    onChange([...entries, { institution: "", degree: "", field: "", year_start: "", year_end: "" }]);
  }

  return (
    <div className="space-y-4">
      {entries.map((entry, i) => (
        <div key={i} className="relative rounded-xl border border-slate-200 bg-slate-50 p-4 space-y-3">
          <button onClick={() => remove(i)}
            className="absolute right-3 top-3 flex items-center justify-center rounded-lg p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-500 transition">
            <Trash2 className="h-3.5 w-3.5" />
          </button>
          <div className="grid gap-3 sm:grid-cols-2 pr-8">
            <Field label="Institution">
              <input className="input" placeholder="e.g. IIT Bombay"
                value={entry.institution} onChange={e => update(i, "institution", e.target.value)} />
            </Field>
            <Field label="Degree">
              <input className="input" placeholder="e.g. B.Tech, M.Sc"
                value={entry.degree} onChange={e => update(i, "degree", e.target.value)} />
            </Field>
            <Field label="Field of Study">
              <input className="input" placeholder="e.g. Computer Science"
                value={entry.field} onChange={e => update(i, "field", e.target.value)} />
            </Field>
            <div className="grid grid-cols-2 gap-2">
              <Field label="Year Start">
                <input className="input" placeholder="e.g. 2018"
                  value={entry.year_start} onChange={e => update(i, "year_start", e.target.value)} />
              </Field>
              <Field label="Year End">
                <input className="input" placeholder="e.g. 2022 / Present"
                  value={entry.year_end} onChange={e => update(i, "year_end", e.target.value)} />
              </Field>
            </div>
          </div>
        </div>
      ))}
      <button onClick={addEntry} className="flex items-center gap-1.5 text-sm font-semibold text-brand-600 hover:text-brand-800 transition">
        <Plus className="h-4 w-4" /> Add Education
      </button>
      {entries.length === 0 && (
        <p className="text-sm text-slate-400 text-center py-2">No education history added yet.</p>
      )}
    </div>
  );
}

/* ── Main Page ──────────────────────────────────────────── */
export function ProfilePage() {
  const [profile, setProfile]       = useState<Profile | null>(null);
  const [draft, setDraft]           = useState<Partial<Profile>>({});
  const [loading, setLoading]       = useState(true);
  const [saving, setSaving]         = useState(false);
  const [activeEdit, setActiveEdit] = useState<SectionId>(null);
  const [toast, setToast]           = useState<{ msg: string; ok: boolean } | null>(null);

  function showToast(msg: string, ok = true) { setToast({ msg, ok }); setTimeout(() => setToast(null), 3000); }

  useEffect(() => {
    apiClient.get<Profile>("/candidates/profile")
      .then(r => { setProfile(r.data); setDraft(r.data); })
      .catch(() => showToast("Could not load profile", false))
      .finally(() => setLoading(false));
  }, []);

  function set<K extends keyof Profile>(key: K, val: Profile[K]) { setDraft(d => ({ ...d, [key]: val })); }

  function startEdit(id: SectionId) {
    if (profile) setDraft({ ...profile });
    setActiveEdit(id);
  }

  function cancelEdit() {
    if (profile) setDraft({ ...profile });
    setActiveEdit(null);
  }

  async function saveSection() {
    setSaving(true);
    try {
      const res = await apiClient.put<Profile>("/candidates/profile/update", draft);
      setProfile(res.data);
      setDraft(res.data);
      setActiveEdit(null);
      showToast("Profile updated successfully");
    } catch { showToast("Save failed. Please try again.", false); }
    finally { setSaving(false); }
  }

  if (loading) return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-slate-300" />
    </div>
  );

  if (!profile) return (
    <div className="mx-auto max-w-lg py-24 text-center">
      <AlertCircle className="mx-auto mb-3 h-12 w-12 text-red-300" />
      <p className="text-base text-slate-600">Could not load your profile. Please try refreshing.</p>
    </div>
  );

  const fullName  = [profile.first_name, profile.last_name].filter(Boolean).join(" ") || profile.email.split("@")[0];
  const inits     = ((profile.first_name?.[0] ?? "") + (profile.last_name?.[0] ?? "")).toUpperCase() || profile.email.slice(0, 2).toUpperCase();
  const pct       = profile.profile_completion_percentage;
  const location  = [profile.city, profile.state, profile.country].filter(Boolean).join(", ");

  const COMPLETION_FIELDS: { key: keyof Profile; label: string }[] = [
    { key: "first_name",        label: "First name" },
    { key: "phone",             label: "Phone number" },
    { key: "city",              label: "City" },
    { key: "current_role",      label: "Current role" },
    { key: "current_company",   label: "Current company" },
    { key: "total_experience",  label: "Total experience" },
    { key: "highest_education", label: "Education" },
    { key: "linkedin_url",      label: "LinkedIn profile" },
  ];
  const missing = COMPLETION_FIELDS.filter(f => {
    const v = profile[f.key];
    return !v || (Array.isArray(v) && v.length === 0);
  });

  const freshBadge = profile.profile_freshness_status === "FRESH" ? "badge-green"
    : profile.profile_freshness_status === "STALE" ? "badge-yellow" : "badge-red";
  const verifiedBadge = profile.verification_status === "verified" ? "badge-green" : "badge-slate";
  const poolBadge     = profile.talent_pool_status === "AVAILABLE" ? "badge-green" : "badge-slate";

  const draftWork = (draft.work_history ?? profile.work_history) as WorkEntry[];
  const draftEdu  = (draft.education_history ?? profile.education_history) as EduEntry[];

  return (
    <div className="mx-auto max-w-[1100px] space-y-6">

      {/* Toast */}
      {toast && (
        <div className={`fixed bottom-6 right-6 z-50 flex items-center gap-2.5 rounded-2xl border px-5 py-3.5 text-sm font-semibold shadow-card-lg animate-fade-in ${toast.ok ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-red-200 bg-red-50 text-red-700"}`}>
          {toast.ok ? <CheckCircle2 className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
          {toast.msg}
        </div>
      )}

      {/* ── Hero Card ─────────────────────────────────────────── */}
      <div className="card overflow-hidden">
        {/* Cover */}
        <div className="relative h-36 bg-gradient-to-r from-brand-700 via-brand-500 to-sky-500">
          <div className="absolute inset-0 opacity-20"
            style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23fff' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E\")" }} />
        </div>

        <div className="px-6 pb-6">
          {/* Avatar + action row */}
          <div className="flex items-end justify-between gap-4 -mt-12">
            <div className="relative">
              <div className="flex h-24 w-24 items-center justify-center rounded-2xl border-4 border-white bg-gradient-to-br from-brand-600 to-sky-500 text-3xl font-extrabold text-white shadow-card-md">
                {inits}
              </div>
              {profile.verification_status === "verified" && (
                <div className="absolute -bottom-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500 ring-2 ring-white">
                  <CheckCircle2 className="h-3.5 w-3.5 text-white" />
                </div>
              )}
            </div>
          </div>

          {/* Name + meta */}
          <div className="mt-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h1 className="text-2xl font-extrabold tracking-tight text-slate-900">{fullName}</h1>
                <p className="mt-0.5 text-base text-slate-500">
                  {profile.current_role ?? <span className="italic text-slate-400">No role set</span>}
                  {profile.current_company && <span className="text-slate-400"> · {profile.current_company}</span>}
                </p>
                {location && (
                  <p className="mt-1 flex items-center gap-1.5 text-sm text-slate-400">
                    <MapPin className="h-3.5 w-3.5" />{location}
                  </p>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                <span className={freshBadge + " badge"}>{profile.profile_freshness_status}</span>
                <span className={verifiedBadge + " badge"}>{profile.verification_status}</span>
                <span className={poolBadge + " badge"}>{profile.talent_pool_status.replace(/_/g, " ")}</span>
              </div>
            </div>

            {pct < 80 && (
              <div className="mt-4 flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3">
                <Sparkles className="h-4 w-4 text-amber-500 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-amber-700">
                  Your profile is <b>{pct}% complete</b>.
                  {missing.length > 0 && <> Add your <b>{missing[0].label}</b>{missing.length > 1 ? ` and ${missing.length - 1} more field${missing.length > 2 ? "s" : ""}` : ""} to get discovered faster.</>}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Two Column Grid ───────────────────────────────────── */}
      <div className="grid gap-6 lg:grid-cols-[300px_1fr]">

        {/* ── LEFT SIDEBAR ──────────────────────────────────── */}
        <div className="space-y-5">

          {/* Completion */}
          <div className="card card-body flex flex-col items-center gap-4 text-center">
            <CompletionRing pct={pct} />
            <div>
              <p className="text-sm font-bold text-slate-800">Profile Strength</p>
              <p className="text-xs text-slate-400 mt-0.5">
                {pct >= 80 ? "Excellent! You stand out to recruiters." : pct >= 50 ? "Good start. A few more details will help." : "Complete your profile to get discovered."}
              </p>
            </div>
            {missing.length > 0 && (
              <div className="w-full rounded-xl bg-slate-50 border border-slate-100 px-4 py-3 text-left space-y-2">
                <p className="text-2xs font-bold uppercase tracking-widest text-slate-400">Missing fields</p>
                {missing.map(f => (
                  <div key={f.key} className="flex items-center gap-2 text-xs text-slate-600">
                    <ChevronRight className="h-3 w-3 text-amber-400 flex-shrink-0" />{f.label}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Contact Section */}
          <Section title="Contact" icon={Phone} editId="personal" activeEdit={activeEdit}
            onEdit={() => startEdit("personal")} onSave={saveSection} onCancel={cancelEdit} saving={saving}>
            {activeEdit === "personal" ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <Field label="First Name">
                    <input className="input" value={draft.first_name ?? ""} onChange={e => set("first_name", e.target.value)} />
                  </Field>
                  <Field label="Last Name">
                    <input className="input" value={draft.last_name ?? ""} onChange={e => set("last_name", e.target.value)} />
                  </Field>
                </div>
                <Field label="Phone">
                  <input className="input" type="tel" placeholder="+91 98765 43210" value={draft.phone ?? ""} onChange={e => set("phone", e.target.value)} />
                </Field>
                <Field label="City">
                  <input className="input" placeholder="e.g. Pune" value={draft.city ?? ""} onChange={e => set("city", e.target.value)} />
                </Field>
                <Field label="State">
                  <input className="input" placeholder="e.g. Maharashtra" value={draft.state ?? ""} onChange={e => set("state", e.target.value)} />
                </Field>
                <Field label="Country">
                  <input className="input" value={draft.country ?? ""} onChange={e => set("country", e.target.value)} />
                </Field>
              </div>
            ) : (
              <div>
                <DetailRow icon={Mail}   label="Email"    value={profile.email} />
                <DetailRow icon={Phone}  label="Phone"    value={profile.phone} />
                <DetailRow icon={MapPin} label="Location" value={location || null} />
              </div>
            )}
          </Section>

          {/* Online Links */}
          <Section title="Online Profiles" icon={Link2} editId="links" activeEdit={activeEdit}
            onEdit={() => startEdit("links")} onSave={saveSection} onCancel={cancelEdit} saving={saving}>
            {activeEdit === "links" ? (
              <div className="space-y-4">
                <Field label="LinkedIn">
                  <input className="input" type="url" placeholder="https://linkedin.com/in/…" value={draft.linkedin_url ?? ""} onChange={e => set("linkedin_url", e.target.value)} />
                </Field>
                <Field label="GitHub">
                  <input className="input" type="url" placeholder="https://github.com/…" value={draft.github_url ?? ""} onChange={e => set("github_url", e.target.value)} />
                </Field>
                <Field label="Portfolio / Website">
                  <input className="input" type="url" placeholder="https://yoursite.com" value={draft.portfolio_url ?? ""} onChange={e => set("portfolio_url", e.target.value)} />
                </Field>
              </div>
            ) : (
              <div>
                {!profile.linkedin_url && !profile.github_url && !profile.portfolio_url ? (
                  <p className="text-sm text-slate-400 italic">No online profiles added yet.</p>
                ) : (
                  <>
                    <DetailRow icon={Linkedin} label="LinkedIn"  value={profile.linkedin_url ? "LinkedIn Profile" : null} href={profile.linkedin_url ?? undefined} />
                    <DetailRow icon={Github}   label="GitHub"    value={profile.github_url   ? "GitHub Profile"   : null} href={profile.github_url ?? undefined} />
                    <DetailRow icon={Globe}    label="Portfolio" value={profile.portfolio_url ? "Portfolio / Site"  : null} href={profile.portfolio_url ?? undefined} />
                  </>
                )}
              </div>
            )}
          </Section>

          {/* Account Details (read-only) */}
          <div className="card card-body">
            <div className="flex items-center gap-2 mb-4">
              <UserRound className="h-4 w-4 text-brand-600" />
              <h2 className="text-sm font-bold text-slate-800">Account Details</h2>
            </div>
            <div className="space-y-3 text-sm">
              {[
                ["Candidate ID",  profile.candidate_id],
                ["Source",        profile.source_type.replace(/_/g, " ")],
                ["Member Since",  fmt(profile.member_since)],
                ["Last Refreshed",fmt(profile.profile_last_refreshed_at)],
              ].map(([l, v]) => (
                <div key={l} className="flex flex-col gap-0.5">
                  <span className="text-2xs font-bold uppercase tracking-widest text-slate-400">{l}</span>
                  <span className="text-slate-700 break-all">{v ?? "—"}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── RIGHT MAIN ──────────────────────────────────────── */}
        <div className="space-y-5">

          {/* Professional Details */}
          <Section title="Professional Details" icon={Briefcase} editId="professional" activeEdit={activeEdit}
            onEdit={() => startEdit("professional")} onSave={saveSection} onCancel={cancelEdit} saving={saving}>
            {activeEdit === "professional" ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Current Role">
                  <input className="input" placeholder="e.g. Senior Developer" value={draft.current_role ?? ""} onChange={e => set("current_role", e.target.value)} />
                </Field>
                <Field label="Current Company">
                  <input className="input" placeholder="e.g. Infosys" value={draft.current_company ?? ""} onChange={e => set("current_company", e.target.value)} />
                </Field>
                <Field label="Total Experience (years)">
                  <input className="input" type="number" min={0} max={50} step={0.5}
                    placeholder="e.g. 5" value={draft.total_experience ?? ""}
                    onChange={e => set("total_experience", e.target.value ? Number(e.target.value) : null)} />
                </Field>
                <Field label="Notice Period">
                  <input className="input" placeholder="e.g. 30 days, Immediate" value={draft.notice_period ?? ""} onChange={e => set("notice_period", e.target.value)} />
                </Field>
                <Field label="Expected Salary (₹)" hint="Enter annual salary in rupees, e.g. 1200000 for ₹12 LPA">
                  <input className="input" type="number" min={0} step={10000}
                    placeholder="e.g. 1200000" value={draft.expected_salary ?? ""}
                    onChange={e => set("expected_salary", e.target.value ? Number(e.target.value) : null)} />
                </Field>
              </div>
            ) : (
              <div className="grid gap-x-8 gap-y-1 sm:grid-cols-2">
                <DetailRow icon={Briefcase}  label="Current Role"     value={profile.current_role} />
                <DetailRow icon={Building2}  label="Current Company"  value={profile.current_company} />
                <DetailRow icon={Star}       label="Experience"       value={profile.total_experience != null ? `${profile.total_experience} years` : null} />
                <DetailRow icon={Clock}      label="Notice Period"    value={profile.notice_period} />
                <DetailRow icon={DollarSign} label="Expected Salary"  value={profile.expected_salary != null ? `₹${(profile.expected_salary / 100000).toFixed(1)} LPA` : null} />
              </div>
            )}
          </Section>

          {/* Skills */}
          <Section title="Skills" icon={Sparkles} editId="skills" activeEdit={activeEdit}
            onEdit={() => startEdit("skills")} onSave={saveSection} onCancel={cancelEdit} saving={saving}>
            {activeEdit === "skills" ? (
              <div className="space-y-3">
                <SkillsEditor value={(draft.skills ?? profile.skills) as string[]} onChange={v => set("skills", v)} />
                <p className="text-2xs text-slate-400">Press Enter or comma to add · Backspace to remove last</p>
              </div>
            ) : (
              profile.skills.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {profile.skills.map(s => (
                    <span key={s} className="inline-flex items-center rounded-full border border-brand-200 bg-brand-50 px-3.5 py-1.5 text-sm font-semibold text-brand-700">{s}</span>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-400 italic">No skills added yet. Add your technical skills to stand out.</p>
              )
            )}
          </Section>

          {/* Work History */}
          <Section title="Work Experience" icon={Building2} editId="work" activeEdit={activeEdit}
            onEdit={() => startEdit("work")} onSave={saveSection} onCancel={cancelEdit} saving={saving}>
            {activeEdit === "work" ? (
              <WorkEntryEditor entries={draftWork} onChange={v => set("work_history", v)} />
            ) : (
              profile.work_history.length > 0 ? (
                <div className="relative space-y-6 pl-6">
                  <div className="absolute left-2.5 top-2 bottom-2 w-px bg-slate-100" />
                  {profile.work_history.map((w, i) => (
                    <div key={i} className="relative">
                      <div className={`absolute -left-[22px] top-1.5 h-4 w-4 rounded-full border-2 border-white shadow-sm ${i === 0 ? "bg-brand-600" : "bg-slate-300"}`} />
                      <p className="font-bold text-slate-900 text-base">{w.role || "—"}</p>
                      <p className="mt-0.5 flex items-center gap-1.5 text-sm text-slate-600">
                        <Building2 className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />{w.company || "—"}
                      </p>
                      {w.duration && (
                        <p className="mt-1 flex items-center gap-1.5 text-xs text-slate-400">
                          <Calendar className="h-3 w-3" />{w.duration}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center gap-3 py-6 text-center">
                  <Briefcase className="h-10 w-10 text-slate-200" />
                  <div>
                    <p className="text-sm font-semibold text-slate-500">No work experience yet</p>
                    <p className="text-xs text-slate-400 mt-0.5">Add your past roles to show recruiters your background.</p>
                  </div>
                </div>
              )
            )}
          </Section>

          {/* Education History */}
          <Section title="Education History" icon={GraduationCap} editId="education" activeEdit={activeEdit}
            onEdit={() => startEdit("education")} onSave={saveSection} onCancel={cancelEdit} saving={saving}>
            {activeEdit === "education" ? (
              <EducationEntryEditor entries={draftEdu} onChange={v => set("education_history", v)} />
            ) : (
              profile.education_history.length > 0 ? (
                <div className="relative space-y-6 pl-6">
                  <div className="absolute left-2.5 top-2 bottom-2 w-px bg-slate-100" />
                  {profile.education_history.map((e, i) => (
                    <div key={i} className="relative">
                      <div className={`absolute -left-[22px] top-1.5 h-4 w-4 rounded-full border-2 border-white shadow-sm ${i === 0 ? "bg-sky-500" : "bg-slate-300"}`} />
                      <p className="font-bold text-slate-900 text-base">{e.degree}{e.field ? ` in ${e.field}` : ""}</p>
                      <p className="mt-0.5 flex items-center gap-1.5 text-sm text-slate-600">
                        <GraduationCap className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />{e.institution || "—"}
                      </p>
                      {(e.year_start || e.year_end) && (
                        <p className="mt-1 flex items-center gap-1.5 text-xs text-slate-400">
                          <Calendar className="h-3 w-3" />
                          {[e.year_start, e.year_end].filter(Boolean).join(" – ")}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center gap-3 py-6 text-center">
                  <GraduationCap className="h-10 w-10 text-slate-200" />
                  <div>
                    <p className="text-sm font-semibold text-slate-500">No education history yet</p>
                    <p className="text-xs text-slate-400 mt-0.5">Add your degrees and certifications.</p>
                  </div>
                </div>
              )
            )}
          </Section>

        </div>
      </div>
    </div>
  );
}
