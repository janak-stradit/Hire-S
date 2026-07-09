"use client";

import { useEffect, useMemo, useState } from "react";
import { Briefcase, Loader2, MapPin, Clock, Search, Bookmark, BookmarkCheck, X } from "lucide-react";
import { apiClient } from "../../api/client";

type Job = {
  requirement_id: string;
  role: string;
  department: string;
  location: string;
  work_mode: string;
  experience_min: number;
  experience_max: number;
  status: string;
};

const WORK_MODES = ["All", "Remote", "Hybrid", "On-site"];

export default function JobsPage() {
  const [allJobs, setAllJobs]   = useState<Job[]>([]);
  const [loading, setLoading]   = useState(true);
  const [search, setSearch]     = useState("");
  const [mode, setMode]         = useState("All");
  const [saved, setSaved]       = useState<Set<string>>(new Set());
  const [applying, setApplying] = useState<string | null>(null);
  const [applied, setApplied]   = useState<Set<string>>(new Set());
  const [toast, setToast]       = useState("");

  function showToast(msg: string) { setToast(msg); setTimeout(() => setToast(""), 2500); }

  useEffect(() => {
    apiClient.get<{ requirements: Job[] }>("/excel-intake/configuration")
      .then(r => setAllJobs((r.data.requirements ?? []).filter((j: Job) => j.status === "active")))
      .catch(() => {}).finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return allJobs.filter(j => {
      const matchSearch = !q || j.role.toLowerCase().includes(q) || j.department.toLowerCase().includes(q) || j.location.toLowerCase().includes(q);
      const matchMode   = mode === "All" || j.work_mode.toLowerCase() === mode.toLowerCase();
      return matchSearch && matchMode;
    });
  }, [allJobs, search, mode]);

  function toggleSave(id: string) {
    setSaved(prev => { const next = new Set(prev); next.has(id) ? next.delete(id) : next.add(id); return next; });
  }

  async function applyNow(job: Job) {
    if (applied.has(job.requirement_id)) return;
    setApplying(job.requirement_id);
    try {
      await apiClient.post("/applications/apply-by-requirement", { requirement_id: job.requirement_id });
      setApplied(prev => new Set(Array.from(prev).concat(job.requirement_id)));
      showToast(`Applied to "${job.role}" successfully!`);
    } catch {
      showToast("Application failed. Please try again.");
    } finally {
      setApplying(null);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 rounded-xl border bg-white px-4 py-3 text-sm font-medium shadow-card-lg animate-fade-in">
          {toast}
        </div>
      )}

      <div>
        <h1 className="page-title flex items-center gap-2"><Briefcase className="h-5 w-5 text-brand-600" /> Open Positions</h1>
        <p className="page-subtitle mt-0.5">{allJobs.length} active opening{allJobs.length !== 1 ? "s" : ""} · Browse and apply below.</p>
      </div>

      {/* Search + filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input className="input pl-10" placeholder="Search by role, department, location…"
            value={search} onChange={e => setSearch(e.target.value)} />
          {search && (
            <button type="button" aria-label="Clear search" onClick={() => setSearch("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        <div className="flex gap-1.5">
          {WORK_MODES.map(m => (
            <button type="button" key={m} onClick={() => setMode(m)}
              className={`rounded-lg px-3 py-2 text-xs font-semibold transition ${mode === m ? "bg-brand-600 text-white" : "border border-slate-200 bg-white text-slate-600 hover:bg-slate-50"}`}>
              {m}
            </button>
          ))}
        </div>
      </div>

      {saved.size > 0 && (
        <div className="flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-2.5 text-xs text-amber-700">
          <BookmarkCheck className="h-4 w-4" />
          <span>{saved.size} saved job{saved.size > 1 ? "s" : ""}</span>
          <button type="button" onClick={() => setSaved(new Set())} className="ml-auto text-amber-500 hover:text-amber-700"><X className="h-3.5 w-3.5" /></button>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-16"><Loader2 className="h-6 w-6 animate-spin text-slate-400" /></div>
      ) : filtered.length === 0 ? (
        <div className="card card-body text-center text-slate-400 py-16">
          <Briefcase className="mx-auto mb-2 h-8 w-8 text-slate-200" />
          {search || mode !== "All" ? "No jobs match your search." : "No open positions at the moment."}
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map(j => {
            const isSaved   = saved.has(j.requirement_id);
            const isApplied = applied.has(j.requirement_id);
            const isApplying = applying === j.requirement_id;
            return (
              <div key={j.requirement_id} className={`card card-body transition-shadow hover:shadow-card-md ${isSaved ? "ring-2 ring-amber-300/60" : ""}`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <div className="flex items-start gap-2">
                      <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-brand-50">
                        <Briefcase className="h-4 w-4 text-brand-600" />
                      </div>
                      <div>
                        <h2 className="text-base font-semibold text-slate-900">{j.role}</h2>
                        <p className="text-sm text-slate-500">{j.department}</p>
                      </div>
                    </div>
                    <div className="mt-2.5 flex flex-wrap gap-2 text-xs text-slate-500">
                      <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{j.location}</span>
                      <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{j.experience_min}–{j.experience_max} yrs exp</span>
                      <span className="badge-slate">{j.work_mode}</span>
                    </div>
                  </div>
                  <div className="flex flex-col gap-2 flex-shrink-0 items-end">
                    <button type="button" onClick={() => toggleSave(j.requirement_id)}
                      className={`rounded-lg p-1.5 transition ${isSaved ? "text-amber-500 bg-amber-50" : "text-slate-400 hover:text-amber-500 hover:bg-amber-50"}`}
                      title={isSaved ? "Remove bookmark" : "Save job"}>
                      {isSaved ? <BookmarkCheck className="h-4 w-4" /> : <Bookmark className="h-4 w-4" />}
                    </button>
                    <button type="button"
                      onClick={() => applyNow(j)}
                      disabled={isApplying || isApplied}
                      className={`text-xs px-3 py-2 rounded-lg font-semibold transition ${isApplied ? "bg-emerald-50 text-emerald-700 border border-emerald-200 cursor-default" : "button-primary"}`}>
                      {isApplying ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : isApplied ? "Applied ✓" : "Apply Now"}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {!loading && filtered.length > 0 && (
        <p className="text-center text-xs text-slate-400">Showing {filtered.length} of {allJobs.length} positions</p>
      )}
    </div>
  );
}
