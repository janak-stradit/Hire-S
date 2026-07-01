"use client";

import {
  Users, Search, RefreshCw, Loader2, X, Mail, Phone, MapPin,
  Briefcase, ExternalLink, Building2,
  ChevronLeft, ChevronRight, Calendar, Download, Copy, Check,
  Filter, SlidersHorizontal, ChevronDown
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { apiClient } from "../../api/client";

type WorkEntry = { role: string; company: string; duration: string };
type Candidate = {
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
  profile_last_refreshed_at: string | null;
  profile_completion_percentage: number;
  source_type: string;
  verification_status: string;
  talent_pool_status: string;
  profile_freshness_status: string;
  is_active: boolean;
  created_at: string;
  last_evaluated_at: string | null;
  last_outcome: string | null;
};

const PAGE_SIZE = 25;

const POOL_OPTIONS   = ["AVAILABLE", "PLACED", "NOT_LOOKING", "BLACKLISTED"];
const FRESH_OPTIONS  = ["FRESH", "STALE", "OUTDATED"];
const SOURCE_OPTIONS = ["resume_intake", "candidate_portal", "excel_import", "manual"];
const EXP_RANGES     = [
  { label: "Any",    min: 0,  max: 99 },
  { label: "0–2 yr", min: 0,  max: 2  },
  { label: "3–5 yr", min: 3,  max: 5  },
  { label: "6–10 yr",min: 6,  max: 10 },
  { label: "10+ yr", min: 10, max: 99 },
];

const FRESH_BADGE: Record<string, string> = {
  FRESH:    "badge-green",
  STALE:    "badge-yellow",
  OUTDATED: "badge-red",
};
const VERIFY_BADGE: Record<string, string> = {
  unverified: "badge-slate",
  verified:   "badge-green",
  flagged:    "badge-red",
};
const POOL_BADGE: Record<string, string> = {
  AVAILABLE:    "badge-green",
  PLACED:       "badge-blue",
  NOT_LOOKING:  "badge-slate",
  BLACKLISTED:  "badge-red",
};

function fmt(d: string | null) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

function fullName(c: Candidate) {
  const n = [c.first_name, c.last_name].filter(Boolean).join(" ");
  return n || c.email.split("@")[0];
}

function initials(c: Candidate) {
  const fn = c.first_name?.[0] ?? "";
  const ln = c.last_name?.[0] ?? "";
  return (fn + ln).toUpperCase() || c.email.slice(0, 2).toUpperCase();
}

/* ── Copy button ─────────────────────────────────────────────── */
function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1500); }}
      className="ml-1.5 text-slate-300 hover:text-slate-600 transition">
      {copied ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
    </button>
  );
}

/* ── Profile panel ──────────────────────────────────────────── */
function ProfilePanel({ candidate: c, onClose, onPoolChange }: {
  candidate: Candidate;
  onClose: () => void;
  onPoolChange: (id: string, status: string) => void;
}) {
  const pct = c.profile_completion_percentage;
  const barColor = pct >= 80 ? "bg-emerald-500" : pct >= 50 ? "bg-amber-500" : "bg-red-500";
  const [poolSaving, setPoolSaving] = useState(false);
  const [showPoolMenu, setShowPoolMenu] = useState(false);
  const poolRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function close(e: MouseEvent) { if (!poolRef.current?.contains(e.target as Node)) setShowPoolMenu(false); }
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  async function changePool(status: string) {
    setShowPoolMenu(false);
    if (status === c.talent_pool_status) return;
    setPoolSaving(true);
    try {
      await apiClient.patch(`/admin/candidates/${c.candidate_id}/pool-status`, { talent_pool_status: status });
      onPoolChange(c.candidate_id, status);
    } catch { /* revert handled by parent reload */ }
    finally { setPoolSaving(false); }
  }

  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <aside className="fixed inset-y-0 right-0 z-50 flex w-full max-w-[500px] flex-col bg-white shadow-card-xl animate-slide-in">
        {/* header */}
        <div className="flex items-start justify-between border-b border-slate-100 px-6 py-5">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 flex-shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500 to-sky-500 text-lg font-bold text-white shadow-md">
              {initials(c)}
            </div>
            <div>
              <div className="flex items-center gap-1">
                <p className="text-base font-bold text-slate-900">{fullName(c)}</p>
                <CopyButton text={fullName(c)} />
              </div>
              <p className="text-xs text-slate-500">{c.current_role ?? "—"} {c.current_company ? `@ ${c.current_company}` : ""}</p>
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                <span className={FRESH_BADGE[c.profile_freshness_status] ?? "badge-slate"}>{c.profile_freshness_status}</span>
                <span className={VERIFY_BADGE[c.verification_status] ?? "badge-slate"}>{c.verification_status}</span>
                <span className={POOL_BADGE[c.talent_pool_status] ?? "badge-slate"}>{c.talent_pool_status}</span>
              </div>
            </div>
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* completion bar */}
        <div className="border-b border-slate-100 px-6 py-3">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-2xs font-semibold uppercase tracking-widest text-slate-400">Profile Completion</span>
            <span className={`text-xs font-bold ${pct >= 80 ? "text-emerald-600" : pct >= 50 ? "text-amber-600" : "text-red-600"}`}>{pct}%</span>
          </div>
          <div className="h-1.5 w-full rounded-full bg-slate-100">
            <div className={`h-1.5 rounded-full ${barColor} transition-all`} style={{ width: `${pct}%` }} />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          <div className="divide-y divide-slate-50 px-6">
            {/* Contact */}
            <section className="py-4 space-y-2">
              <p className="section-label">Contact</p>
              <div className="space-y-1.5">
                <div className="flex items-center gap-2.5">
                  <a href={`mailto:${c.email}`} className="flex items-center gap-2 text-sm text-slate-700 hover:text-brand-600 transition group">
                    <Mail className="h-4 w-4 flex-shrink-0 text-slate-400 group-hover:text-brand-500" />{c.email}
                  </a>
                  <CopyButton text={c.email} />
                </div>
                {c.phone && (
                  <div className="flex items-center gap-2.5">
                    <a href={`tel:${c.phone}`} className="flex items-center gap-2 text-sm text-slate-700 hover:text-brand-600 transition group">
                      <Phone className="h-4 w-4 flex-shrink-0 text-slate-400 group-hover:text-brand-500" />{c.phone}
                    </a>
                    <CopyButton text={c.phone} />
                  </div>
                )}
                {(c.city || c.state || c.country) && (
                  <div className="flex items-center gap-2.5 text-sm text-slate-600">
                    <MapPin className="h-4 w-4 flex-shrink-0 text-slate-400" />
                    {[c.city, c.state, c.country].filter(Boolean).join(", ")}
                  </div>
                )}
              </div>
            </section>

            {/* Professional */}
            <section className="py-4 space-y-2">
              <p className="section-label">Professional</p>
              <div className="grid grid-cols-2 gap-3 text-sm">
                {([
                  ["Role",        c.current_role],
                  ["Company",     c.current_company],
                  ["Experience",  c.total_experience != null ? `${c.total_experience} yrs` : null],
                  ["Notice",      c.notice_period],
                  ["Salary",      c.expected_salary != null ? `₹${(c.expected_salary/100000).toFixed(1)} L` : null],
                  ["Education",   c.highest_education],
                ] as [string, string | null][]).map(([label, val]) => val ? (
                  <div key={label}>
                    <p className="text-2xs font-semibold uppercase tracking-wider text-slate-400">{label}</p>
                    <p className="mt-0.5 font-medium text-slate-800 break-words">{val}</p>
                  </div>
                ) : null)}
              </div>
            </section>

            {/* Skills */}
            {c.skills.length > 0 && (
              <section className="py-4 space-y-2">
                <p className="section-label">Skills <span className="text-slate-400 font-normal">({c.skills.length})</span></p>
                <div className="flex flex-wrap gap-1.5">
                  {c.skills.map(s => (
                    <span key={s} className="inline-flex items-center rounded-full border border-brand-100 bg-brand-50 px-2.5 py-0.5 text-xs font-medium text-brand-700">{s}</span>
                  ))}
                </div>
              </section>
            )}

            {/* Work History */}
            {c.work_history.length > 0 && (
              <section className="py-4 space-y-3">
                <p className="section-label">Work History <span className="text-slate-400 font-normal">({c.work_history.length} roles)</span></p>
                <div className="relative space-y-4 pl-4">
                  <div className="absolute inset-y-0 left-1.5 w-px bg-slate-100" />
                  {c.work_history.map((w, i) => (
                    <div key={i} className="relative">
                      <div className={`absolute -left-[11px] top-1 h-2.5 w-2.5 rounded-full border-2 border-white ${i === 0 ? "bg-brand-600 shadow-sm" : "bg-slate-300"}`} />
                      <p className="text-sm font-semibold text-slate-800">{w.role}</p>
                      <p className="text-xs text-slate-600 flex items-center gap-1.5">
                        <Building2 className="h-3 w-3 text-slate-400" />{w.company}
                      </p>
                      {w.duration && <p className="mt-0.5 text-2xs text-slate-400 flex items-center gap-1"><Calendar className="h-3 w-3" />{w.duration}</p>}
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Online Profiles */}
            {(c.linkedin_url || c.github_url || c.portfolio_url) && (
              <section className="py-4 space-y-2">
                <p className="section-label">Online Profiles</p>
                <div className="space-y-1.5">
                  {[["LinkedIn", c.linkedin_url], ["GitHub", c.github_url], ["Portfolio", c.portfolio_url]].map(([label, url]) =>
                    url ? (
                      <a key={label as string} href={url as string} target="_blank" rel="noopener noreferrer"
                        className="flex items-center gap-2 text-sm text-brand-600 hover:underline">
                        <ExternalLink className="h-3.5 w-3.5" />{label}
                      </a>
                    ) : null
                  )}
                </div>
              </section>
            )}

            {/* Record Details */}
            <section className="py-4 space-y-2">
              <p className="section-label">Record Details</p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {([
                  ["Candidate ID",  c.candidate_id.slice(0, 12) + "…"],
                  ["Source",        c.source_type],
                  ["Created",       fmt(c.created_at)],
                  ["Last Updated",  fmt(c.profile_last_refreshed_at)],
                  ["Last Eval",     fmt(c.last_evaluated_at)],
                  ["Last Outcome",  c.last_outcome ?? "—"],
                  ["Active",        c.is_active ? "Yes" : "No"],
                ] as [string, string][]).map(([l, v]) => (
                  <div key={l}>
                    <p className="font-semibold uppercase tracking-wider text-slate-400" style={{fontSize:"0.625rem"}}>{l}</p>
                    <p className="mt-0.5 text-slate-700">{v}</p>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </div>

        {/* footer */}
        <div className="border-t border-slate-100 px-6 py-3 flex items-center gap-2">
          <a href={`mailto:${c.email}`} className="button-secondary flex-1 justify-center text-xs"><Mail className="h-3.5 w-3.5" /> Email</a>
          {c.phone && <a href={`tel:${c.phone}`} className="button-secondary flex-1 justify-center text-xs"><Phone className="h-3.5 w-3.5" /> Call</a>}
          <div ref={poolRef} className="relative">
            <button onClick={() => setShowPoolMenu(v => !v)} disabled={poolSaving}
              className="button-primary text-xs justify-center gap-1">
              {poolSaving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <>Pool Status <ChevronDown className="h-3.5 w-3.5" /></>}
            </button>
            {showPoolMenu && (
              <div className="absolute bottom-full right-0 mb-1 min-w-[150px] rounded-xl border border-slate-200 bg-white py-1 shadow-card-lg z-10">
                {POOL_OPTIONS.map(s => (
                  <button key={s} onClick={() => changePool(s)}
                    className={`flex w-full items-center gap-2 px-3 py-1.5 text-xs font-medium hover:bg-slate-50 ${s === c.talent_pool_status ? "text-brand-600" : "text-slate-700"}`}>
                    <span className={`h-1.5 w-1.5 rounded-full ${s === "AVAILABLE" ? "bg-emerald-500" : s === "PLACED" ? "bg-blue-500" : s === "NOT_LOOKING" ? "bg-slate-400" : "bg-red-500"}`} />
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  );
}

/* ── Main page ──────────────────────────────────────────────── */
export default function CandidateMasterPage() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [total, setTotal]       = useState(0);
  const [page, setPage]         = useState(1);
  const [search, setSearch]     = useState("");
  const [poolFilter, setPool]   = useState("");
  const [freshFilter, setFresh] = useState("");
  const [sourceFilter, setSrc]  = useState("");
  const [expIdx, setExpIdx]     = useState(0);
  const [loading, setLoading]   = useState(true);
  const [selected, setSelected] = useState<Candidate | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const expRange   = EXP_RANGES[expIdx];

  const load = useCallback(async (p: number, q: string, pool: string, fresh: string, src: string, expI: number) => {
    setLoading(true);
    const exp = EXP_RANGES[expI];
    try {
      const res = await apiClient.get("/admin/candidates-master", {
        params: {
          limit: PAGE_SIZE,
          offset: (p - 1) * PAGE_SIZE,
          search: q || undefined,
          talent_pool_status: pool || undefined,
          freshness_status: fresh || undefined,
          source_type: src || undefined,
        },
      });
      setCandidates(res.data.items ?? []);
      setTotal(res.data.total ?? 0);
    } catch {
      setCandidates([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(page, search, poolFilter, freshFilter, sourceFilter, expIdx);
  }, [load, page, search, poolFilter, freshFilter, sourceFilter, expIdx]);

  function resetFilters() { setPool(""); setFresh(""); setSrc(""); setExpIdx(0); setPage(1); }
  const hasFilters = !!(poolFilter || freshFilter || sourceFilter || expIdx > 0);

  function handleSearch(q: string) { setSearch(q); setPage(1); }

  function updatePoolStatus(candidateId: string, status: string) {
    setCandidates(prev => prev.map(c => c.candidate_id === candidateId ? { ...c, talent_pool_status: status } : c));
    if (selected?.candidate_id === candidateId) setSelected(p => p ? { ...p, talent_pool_status: status } : p);
  }

  function exportCSV() {
    const headers = ["Name","Email","Phone","City","Role","Company","Experience","Notice","Salary","Education","Skills","Pool Status","Freshness","Last Updated"];
    const rows = candidates.map(c => [
      fullName(c), c.email, c.phone ?? "", [c.city, c.state].filter(Boolean).join(" "),
      c.current_role ?? "", c.current_company ?? "",
      c.total_experience != null ? `${c.total_experience} yrs` : "",
      c.notice_period ?? "",
      c.expected_salary != null ? `${(c.expected_salary/100000).toFixed(1)} L` : "",
      c.highest_education ?? "",
      c.skills.join("; "),
      c.talent_pool_status, c.profile_freshness_status, fmt(c.profile_last_refreshed_at),
    ]);
    const csv = [headers, ...rows].map(r => r.map(v => `"${String(v).replace(/"/g,'""')}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a"); a.href = url; a.download = "hirex_candidates.csv"; a.click();
    URL.revokeObjectURL(url);
  }

  function pages(): (number | "…")[] {
    if (totalPages <= 7) return Array.from({ length: totalPages }, (_, i) => i + 1);
    const left  = Math.max(2, page - 1);
    const right = Math.min(totalPages - 1, page + 1);
    const out: (number | "…")[] = [1];
    if (left > 2) out.push("…");
    for (let i = left; i <= right; i++) out.push(i);
    if (right < totalPages - 1) out.push("…");
    out.push(totalPages);
    return out;
  }

  return (
    <div className="mx-auto max-w-[1400px] space-y-5">
      {selected && (
        <ProfilePanel
          candidate={selected}
          onClose={() => setSelected(null)}
          onPoolChange={updatePoolStatus}
        />
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title flex items-center gap-2"><Users className="h-5 w-5 text-brand-600" /> Candidate Master</h1>
          <p className="page-subtitle mt-0.5">{total.toLocaleString()} candidates · Page {page} of {totalPages}</p>
        </div>
        <div className="flex gap-2">
          <button onClick={exportCSV} className="button-secondary" title="Export CSV">
            <Download className="h-4 w-4" /> Export
          </button>
          <button onClick={() => setShowFilters(v => !v)}
            className={`button-secondary ${hasFilters ? "ring-2 ring-brand-400" : ""}`}>
            <SlidersHorizontal className="h-4 w-4" /> Filters {hasFilters && <span className="ml-1 rounded-full bg-brand-600 px-1.5 py-0.5 text-2xs text-white">ON</span>}
          </button>
          <button onClick={() => load(page, search, poolFilter, freshFilter, sourceFilter, expIdx)} disabled={loading} className="button-secondary">
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input className="input pl-10" placeholder="Search by name, email, role, company, skills…"
          value={search} onChange={e => handleSearch(e.target.value)} />
      </div>

      {/* Filter panel */}
      {showFilters && (
        <div className="card card-body animate-fade-in">
          <div className="flex flex-wrap gap-4 items-end">
            <div className="space-y-1 min-w-[160px]">
              <label className="text-xs font-semibold text-slate-600 flex items-center gap-1"><Filter className="h-3 w-3" /> Pool Status</label>
              <select className="input text-sm" value={poolFilter} onChange={e => { setPool(e.target.value); setPage(1); }}>
                <option value="">All</option>
                {POOL_OPTIONS.map(o => <option key={o} value={o}>{o}</option>)}
              </select>
            </div>
            <div className="space-y-1 min-w-[140px]">
              <label className="text-xs font-semibold text-slate-600">Freshness</label>
              <select className="input text-sm" value={freshFilter} onChange={e => { setFresh(e.target.value); setPage(1); }}>
                <option value="">All</option>
                {FRESH_OPTIONS.map(o => <option key={o} value={o}>{o}</option>)}
              </select>
            </div>
            <div className="space-y-1 min-w-[160px]">
              <label className="text-xs font-semibold text-slate-600">Source</label>
              <select className="input text-sm" value={sourceFilter} onChange={e => { setSrc(e.target.value); setPage(1); }}>
                <option value="">All</option>
                {SOURCE_OPTIONS.map(o => <option key={o} value={o}>{o.replace(/_/g," ")}</option>)}
              </select>
            </div>
            <div className="space-y-1 min-w-[140px]">
              <label className="text-xs font-semibold text-slate-600">Experience</label>
              <select className="input text-sm" value={expIdx} onChange={e => { setExpIdx(Number(e.target.value)); setPage(1); }}>
                {EXP_RANGES.map((r, i) => <option key={i} value={i}>{r.label}</option>)}
              </select>
            </div>
            {hasFilters && (
              <button onClick={resetFilters} className="button-secondary text-xs h-fit">
                <X className="h-3.5 w-3.5" /> Clear Filters
              </button>
            )}
          </div>
          {hasFilters && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {poolFilter  && <span className="badge-blue">Pool: {poolFilter}</span>}
              {freshFilter && <span className="badge-yellow">Freshness: {freshFilter}</span>}
              {sourceFilter && <span className="badge-slate">Source: {sourceFilter.replace(/_/g," ")}</span>}
              {expIdx > 0  && <span className="badge-purple">Exp: {expRange.label}</span>}
            </div>
          )}
        </div>
      )}

      <div className="card overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-20"><Loader2 className="h-6 w-6 animate-spin text-slate-400" /></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Contact</th>
                  <th>Role / Company</th>
                  <th>Exp</th>
                  <th>Notice</th>
                  <th>Location</th>
                  <th>Skills</th>
                  <th>Freshness</th>
                  <th>Last Updated</th>
                  <th>Pool Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {candidates.length === 0 && (
                  <tr>
                    <td colSpan={11} className="py-20 text-center text-slate-400">
                      <Users className="mx-auto mb-2 h-8 w-8 text-slate-200" />
                      {search || hasFilters ? "No candidates match your filters" : "No candidates yet"}
                    </td>
                  </tr>
                )}
                {candidates.map(c => (
                  <tr key={c.candidate_id} className="cursor-pointer" onClick={() => setSelected(c)}>
                    <td>
                      <div className="flex items-center gap-2.5">
                        <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand-400 to-sky-500 text-xs font-bold text-white">
                          {initials(c)}
                        </div>
                        <div>
                          <p className="font-semibold text-slate-800">{fullName(c)}</p>
                          <p className="text-2xs text-slate-400">{c.candidate_id.slice(0, 8)}…</p>
                        </div>
                      </div>
                    </td>
                    <td>
                      <div className="space-y-0.5">
                        <p className="text-xs text-slate-600">{c.email}</p>
                        {c.phone && <p className="text-xs text-slate-400">{c.phone}</p>}
                      </div>
                    </td>
                    <td>
                      <p className="text-xs font-medium text-slate-700">{c.current_role ?? "—"}</p>
                      <p className="text-2xs text-slate-400">{c.current_company ?? ""}</p>
                    </td>
                    <td className="text-xs text-slate-600">{c.total_experience != null ? `${c.total_experience} yr` : "—"}</td>
                    <td className="text-xs text-slate-500">{c.notice_period ?? "—"}</td>
                    <td className="text-xs text-slate-500">{[c.city, c.state].filter(Boolean).join(", ") || "—"}</td>
                    <td>
                      <div className="flex flex-wrap gap-1 max-w-[160px]">
                        {c.skills.slice(0, 3).map(s => (
                          <span key={s} className="inline-flex items-center rounded-full bg-brand-50 px-2 py-0.5 text-2xs font-medium text-brand-700">{s}</span>
                        ))}
                        {c.skills.length > 3 && (
                          <span className="text-2xs text-slate-400">+{c.skills.length - 3}</span>
                        )}
                      </div>
                    </td>
                    <td>
                      <span className={FRESH_BADGE[c.profile_freshness_status] ?? "badge-slate"}>
                        {c.profile_freshness_status}
                      </span>
                    </td>
                    <td className="text-xs text-slate-400">{fmt(c.profile_last_refreshed_at)}</td>
                    <td>
                      <span className={POOL_BADGE[c.talent_pool_status] ?? "badge-slate"}>
                        {c.talent_pool_status}
                      </span>
                    </td>
                    <td onClick={e => { e.stopPropagation(); setSelected(c); }}>
                      <button className="button-secondary py-1 px-2.5 text-xs">View</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-1">
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="button-secondary px-2.5 py-2">
            <ChevronLeft className="h-4 w-4" />
          </button>
          {pages().map((p, i) =>
            p === "…" ? (
              <span key={`e${i}`} className="px-3 py-2 text-sm text-slate-400">…</span>
            ) : (
              <button key={p} onClick={() => setPage(p as number)}
                className={`min-w-[36px] rounded-lg px-3 py-2 text-sm font-medium transition ${page === p ? "bg-brand-600 text-white shadow-sm" : "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50"}`}>
                {p}
              </button>
            )
          )}
          <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="button-secondary px-2.5 py-2">
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
}
