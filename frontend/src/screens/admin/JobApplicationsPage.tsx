"use client";

import {
  Users, Search, RefreshCw, Loader2, ArrowLeft, Download, SlidersHorizontal, Filter,
  Building2, MapPin, X, Check, Copy, ChevronLeft, ChevronRight, Briefcase, ChevronDown, Zap
} from "lucide-react";
import { useCallback, useEffect, useState, useRef } from "react";
import { apiClient } from "../../api/client";
import { useRouter, useSearchParams } from "next/navigation";

type CandidateRow = {
  application_id: string;
  validator_result_id: string;
  candidate_id: string;
  name: string;
  email: string;
  current_role: string | null;
  location: string;
  experience_years: number;
  job_id: string;
  job_title: string;
  final_score: number;
  validator_decision: string;
  queue_target: string;
  application_status: string;
  hr_action: string | null;
  source_type: string;
  verification_status: string;
  evaluated_at: string;
};

const PAGE_SIZE = 25;

const DECISIONS = ["PASS", "REVIEW"];
const HR_ACTIONS = ["MOVE_FORWARD", "HOLD"];
const WORKFLOW_STATES = ["PENDING", "MOVE_FORWARD", "HOLD"];

const DECISION_BADGE: Record<string, string> = {
  PASS: "badge-green",
  REVIEW: "badge-yellow",
  FAIL: "badge-red",
};

const HR_ACTION_BADGE: Record<string, string> = {
  MOVE_FORWARD: "badge-green",
  HOLD: "badge-yellow",
};

function fmt(d: string | null) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

export default function JobApplicationsPage({ jobId, initialDecision }: { jobId?: string; initialDecision?: string }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [candidates, setCandidates] = useState<CandidateRow[]>([]);
  const [total, setTotal]       = useState(0);
  const [page, setPage]         = useState(1);
  const [search, setSearch]     = useState("");
  
  const [decision, setDecision] = useState(initialDecision || searchParams.get("decision") || "");
  const [hrAction, setHrAction] = useState("");
  const [workflow, setWorkflow] = useState("");
  const [selectedJob, setSelectedJob] = useState("");
  
  const [loading, setLoading]   = useState(true);
  const [jobTitle, setJobTitle] = useState("");
  const [activeJobs, setActiveJobs] = useState<{job_id: string, title: string}[]>([]);
  const [showFilters, setShowFilters] = useState(false);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const hasFilters = Boolean(decision || hrAction || workflow);

  useEffect(() => {
    if (jobId) {
      apiClient.get(`/jobs/${jobId}`).then(res => setJobTitle(res.data.title)).catch(() => {});
    } else {
      apiClient.get(`/jobs/list`).then(res => setActiveJobs(res.data.jobs || [])).catch(() => {});
    }
  }, [jobId]);

  const load = useCallback(async (p: number, q: string, dec: string, hrAct: string, flow: string, jId: string) => {
    setLoading(true);
    try {
      const res = await apiClient.get("/admin/candidates", {
        params: {
          job_id: jobId || jId || undefined,
          limit: PAGE_SIZE,
          offset: (p - 1) * PAGE_SIZE,
          search: q || undefined,
          decision: dec || undefined,
          hr_action: hrAct || undefined,
          workflow_state: flow || undefined,
        },
      });
      setCandidates(res.data.items ?? []);
      setTotal(res.data.total ?? 0);
    } catch {
      setCandidates([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    const timer = setTimeout(() => {
      load(page, search, decision, hrAction, workflow, selectedJob);
    }, 300);
    return () => clearTimeout(timer);
  }, [page, search, decision, hrAction, workflow, selectedJob, load]);

  function handleSearch(val: string) { setSearch(val); setPage(1); }

  function resetFilters() {
    setDecision("");
    setHrAction("");
    setWorkflow("");
    setSelectedJob("");
    setPage(1);
    setSearch("");
  }

  function exportCSV() {
    if (candidates.length === 0) return;
    const headers = [
      "Name", "Email", "Current Role", "Location", "Experience (yrs)", 
      "Final Score", "Validator Decision", "HR Action", "Application Status", "Evaluated At"
    ];
    const rows = candidates.map(c => [
      c.name, c.email, c.current_role ?? "", c.location ?? "", c.experience_years,
      c.final_score, c.validator_decision, c.hr_action ?? "", c.application_status, fmt(c.evaluated_at)
    ]);
    const csv = [headers, ...rows].map(r => r.map(v => `"${String(v).replace(/"/g,'""')}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a"); a.href = url; a.download = `job_${jobId}_applications.csv`; a.click();
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
    <div className="mx-auto max-w-[1400px] space-y-5 animate-fade-in">
      <button onClick={() => jobId ? router.push("/job-posts") : router.push("/operations")}
        className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 transition">
        <ArrowLeft className="h-4 w-4" /> Back to {jobId ? "Job Posts" : "Dashboard"}
      </button>

      <div className="flex items-end justify-between">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <Briefcase className="h-5 w-5 text-brand-600" /> 
            {jobId ? `Applications ${jobTitle ? `for ${jobTitle}` : ""}` : "All Applications"}
          </h1>
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
          <button onClick={() => load(page, search, decision, hrAction, workflow, selectedJob)} disabled={loading} className="button-secondary">
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input className="input pl-10" placeholder="Search by name, email, role…"
          value={search} onChange={e => handleSearch(e.target.value)} />
      </div>

      {/* Filter panel */}
      {showFilters && (
        <div className="card card-body animate-fade-in">
          <div className="flex flex-wrap gap-4 items-end">
            {!jobId && (
              <div className="space-y-1 min-w-[200px]">
                <label className="text-xs font-semibold text-slate-600 flex items-center gap-1"><Briefcase className="h-3 w-3" /> Job Post</label>
                <select className="input text-sm" value={selectedJob} onChange={e => { setSelectedJob(e.target.value); setPage(1); }}>
                  <option value="">All Jobs</option>
                  {activeJobs.map(j => <option key={j.job_id} value={j.job_id}>{j.title}</option>)}
                </select>
              </div>
            )}
            <div className="space-y-1 min-w-[160px]">
              <label className="text-xs font-semibold text-slate-600 flex items-center gap-1"><Filter className="h-3 w-3" /> Decision</label>
              <select className="input text-sm" value={decision} onChange={e => { setDecision(e.target.value); setPage(1); }}>
                <option value="">All</option>
                {DECISIONS.map(o => <option key={o} value={o}>{o}</option>)}
              </select>
            </div>
            <div className="space-y-1 min-w-[160px]">
              <label className="text-xs font-semibold text-slate-600">HR Action</label>
              <select className="input text-sm" value={hrAction} onChange={e => { setHrAction(e.target.value); setPage(1); }}>
                <option value="">All</option>
                {HR_ACTIONS.map(o => <option key={o} value={o}>{o.replace(/_/g," ")}</option>)}
              </select>
            </div>
            <div className="space-y-1 min-w-[160px]">
              <label className="text-xs font-semibold text-slate-600">Workflow State</label>
              <select className="input text-sm" value={workflow} onChange={e => { setWorkflow(e.target.value); setPage(1); }}>
                <option value="">All</option>
                {WORKFLOW_STATES.map(o => <option key={o} value={o}>{o.replace(/_/g," ")}</option>)}
              </select>
            </div>
            {hasFilters && (
              <button onClick={resetFilters} className="button-secondary text-xs h-fit">
                <X className="h-3.5 w-3.5" /> Clear Filters
              </button>
            )}
          </div>
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
                  {!jobId && <th>Job Role</th>}
                  <th>Role</th>
                  <th>Location</th>
                  <th>Exp</th>
                  <th>Score</th>
                  <th>Validator Decision</th>
                  <th>HR Action</th>
                  <th>Status</th>
                  <th>Evaluated At</th>
                  <th>Vapi Interview</th>
                </tr>
              </thead>
              <tbody>
                {candidates.length === 0 && (
                  <tr>
                    <td colSpan={10} className="py-20 text-center text-slate-400">
                      <Users className="mx-auto mb-2 h-8 w-8 text-slate-200" />
                      {search || hasFilters ? "No applications match your filters" : "No applications yet"}
                    </td>
                  </tr>
                )}
                {candidates.map(c => (
                  <tr key={c.application_id} className="hover:bg-slate-50">
                    <td>
                      <div className="font-semibold text-slate-800">{c.name}</div>
                      <div className="text-xs text-slate-500">{c.email}</div>
                    </td>
                    {!jobId && (
                      <td className="text-brand-600 font-medium text-xs max-w-[180px] truncate" title={c.job_title}>{c.job_title}</td>
                    )}
                    <td className="text-slate-600">{c.current_role ?? "—"}</td>
                    <td className="text-slate-600">{c.location || "—"}</td>
                    <td>{c.experience_years ? `${c.experience_years.toFixed(1)} yrs` : "—"}</td>
                    <td>
                      <div className={`font-semibold ${c.final_score >= 80 ? 'text-emerald-600' : c.final_score >= 50 ? 'text-amber-600' : 'text-red-600'}`}>
                        {c.final_score.toFixed(0)}%
                      </div>
                    </td>
                    <td>
                      <span className={DECISION_BADGE[c.validator_decision] ?? "badge-slate"}>
                        {c.validator_decision}
                      </span>
                    </td>
                    <td>
                      {c.validator_decision === "REVIEW" ? (
                        <HrActionCell appId={c.application_id} currentAction={c.hr_action} onRefresh={() => load(page, search, decision, hrAction, workflow, selectedJob)} />
                      ) : (
                        <span className="text-slate-400 text-sm">—</span>
                      )}
                    </td>
                    <td>
                      <span className="badge-slate">
                        {(c.application_status === "R1_READY" || c.application_status.toLowerCase() === "shortlisted") ? "R1 Ready" : c.application_status}
                      </span>
                    </td>
                    <td className="text-xs text-slate-500">{fmt(c.evaluated_at)}</td>
                    <td>
                      {(c.application_status === "R1_READY" || c.application_status.toLowerCase() === "shortlisted") && (
                        <ScheduleVapiInterviewButton appId={c.application_id} />
                      )}
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
          {pages().map((p, i) => p === "…" ? (
            <span key={`ell-${i}`} className="px-2 text-slate-400">…</span>
          ) : (
            <button key={p} onClick={() => setPage(p as number)}
              className={`min-w-[36px] rounded-lg px-3 py-2 text-sm font-medium transition ${page === p ? "bg-brand-600 text-white" : "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50"}`}>
              {p}
            </button>
          ))}
          <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="button-secondary px-2.5 py-2">
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
}

function HrActionCell({ appId, currentAction, onRefresh }: { appId: string, currentAction: string | null, onRefresh: () => void }) {
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function close(e: MouseEvent) { if (!ref.current?.contains(e.target as Node)) setOpen(false); }
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  async function pick(a: string) {
    setOpen(false);
    if (a === currentAction) return;
    setSaving(true);
    try {
      await apiClient.post(`/admin/candidates/${appId}/decision`, { action: a, reason: "Quick action from dashboard" });
      onRefresh();
    } catch {
      alert("Failed to save action");
    } finally {
      setSaving(false);
    }
  }

  const ACTIONS = ["MOVE_FORWARD", "HOLD"];
  
  return (
    <div ref={ref} className="relative inline-block">
      <button onClick={e => { e.stopPropagation(); setOpen(o => !o); }}
        disabled={saving}
        className={`${currentAction ? (HR_ACTION_BADGE[currentAction] ?? "badge-slate") : "badge-slate bg-slate-100 text-slate-600 hover:bg-slate-200"} inline-flex items-center gap-1 cursor-pointer transition`}>
        {saving ? <Loader2 className="h-3 w-3 animate-spin" /> : (currentAction ? currentAction.replace("_", " ") : "Action")}
        <ChevronDown className="h-3 w-3" />
      </button>
      {open && (
        <div className="absolute left-0 top-full z-20 mt-1 min-w-[140px] rounded-xl border border-slate-200 bg-white shadow-card-lg py-1">
          {ACTIONS.map(a => (
            <button key={a} onClick={(e) => { e.stopPropagation(); pick(a); }}
              className={`flex w-full items-center gap-2 px-3 py-2 text-xs font-medium hover:bg-slate-50 ${a === currentAction ? "text-brand-600 bg-brand-50" : "text-slate-700"}`}>
              {a.replace("_", " ")}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function ScheduleVapiInterviewButton({ appId }: { appId: string }) {
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<string>("none");
  const [webCallUrl, setWebCallUrl] = useState<string | null>(null);
  const [vapiData, setVapiData] = useState<any>(null);

  useEffect(() => {
    checkStatus();
  }, [appId]);

  useEffect(() => {
    let interval: any;
    if (status === "queued" || status === "in-progress") {
      interval = setInterval(checkStatus, 3000);
    }
    return () => clearInterval(interval);
  }, [status]);

  async function checkStatus() {
    try {
      const res = await apiClient.get(`/admin/candidates/${appId}/vapi-status`);
      const data = res.data;
      if (data.status !== "none") {
        setStatus(data.status);
        if (data.web_call_url) setWebCallUrl(data.web_call_url);
        if (data.status === "ended") setVapiData(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function scheduleInterview() {
    setLoading(true);
    try {
      const res = await apiClient.post(`/admin/candidates/${appId}/vapi-schedule`);
      setStatus("queued");
      setWebCallUrl(res.data.web_call_url);
    } catch (err: any) {
      alert("Failed to schedule Vapi interview: " + (err?.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div className="h-7 flex items-center justify-center"><Loader2 className="h-4 w-4 animate-spin text-slate-400" /></div>;

  if (status === "ended" && vapiData) {
    return (
      <div className="flex flex-col gap-1 items-start">
        <span className="inline-flex items-center gap-1 text-[10px] font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
          <Check className="h-3 w-3" /> Completed
        </span>
        <button onClick={() => alert("Transcript:\n\n" + (vapiData.transcript || "No transcript available."))} className="text-[10px] text-brand-600 hover:underline">
          View Transcript
        </button>
        {vapiData.recording_url && (
          <a href={vapiData.recording_url} target="_blank" rel="noreferrer" className="text-[10px] text-blue-600 hover:underline">
            Listen Audio
          </a>
        )}
      </div>
    );
  }

  if (status === "queued" || status === "in-progress") {
    return (
      <div className="flex flex-col gap-1 items-start">
        <span className="inline-flex items-center gap-1 text-[10px] font-medium text-amber-600 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
          <Loader2 className="h-3 w-3 animate-spin" /> {status === "in-progress" ? "In Progress" : "Queued"}
        </span>
        {webCallUrl && (
          <a href={webCallUrl} target="_blank" rel="noreferrer" className="text-[10px] text-brand-600 hover:underline font-medium flex items-center gap-1 mt-0.5">
            <Zap className="h-3 w-3 text-brand-500 fill-brand-500" /> Join Call
          </a>
        )}
      </div>
    );
  }

  return (
    <button
      onClick={scheduleInterview}
      disabled={loading}
      className="button-primary text-xs h-7 px-3 bg-brand-600 hover:bg-brand-700 text-white border-transparent whitespace-nowrap shadow-sm shadow-brand-600/20"
    >
      Schedule R1 Interview
    </button>
  );
}
