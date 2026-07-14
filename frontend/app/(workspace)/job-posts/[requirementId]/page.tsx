"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState, useRef, useCallback } from "react";
import {
  ArrowLeft, Briefcase, MapPin, Clock, DollarSign, GraduationCap,
  Award, Users, CheckCircle2, Loader2, ChevronDown,
  ScanSearch, User, Zap, XCircle, TrendingUp, Download, Filter, X, SlidersHorizontal, Check
} from "lucide-react";
import { apiClient } from "../../../../src/api/client";

type Job = {
  job_id: string;
  title: string;
  department: string;
  location: string;
  employment_type: string;
  experience_min: number | null;
  experience_max: number | null;
  salary_min: number | null;
  salary_max: number | null;
  description: string;
  skills_required: string[];
  preferred_skills: string[];
  education_requirements: string;
  mandatory_certifications: string[];
  status: string;
  total_applications: number;
  screening_pass_score: number | null;
  screening_review_score: number | null;
};

type MatchedCandidate = {
  candidate_id: string;
  name: string;
  phone: string | null;
  city: string | null;
  state: string | null;
  freshness: string;
  experience_years: number;
  matched_skills: string[];
  missing_skills: string[];
  match_score: number;
  total_required: number;
  decision: string;
  is_imported?: boolean;
  application_id?: string;
  application_status?: string;
  hr_action?: string;
};

type ScanResult = {
  job_title: string;
  total_matches: number;
  candidates: MatchedCandidate[];
};

const STATUS_BADGE: Record<string, string> = {
  open:   "badge-green",
  draft:  "badge-purple",
  closed: "badge-slate",
  paused: "badge-yellow",
};

const STATUSES = ["open", "draft", "paused", "closed"];

const HR_ACTION_BADGE: Record<string, string> = {
  MOVE_FORWARD: "badge-green",
  HOLD: "badge-yellow",
  REJECT: "badge-red"
};

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

const FRESHNESS_BADGE: Record<string, string> = {
  FRESH:  "badge-green",
  STALE:  "badge-yellow",
  AGED:   "badge-red",
};

function fmtSalary(n: number | null) {
  if (n == null) return null;
  return `₹${(n / 100000).toFixed(1)} LPA`;
}

function MatchBar({ score }: { score: number }) {
  const color = score >= 70 ? "bg-emerald-500" : score >= 40 ? "bg-amber-400" : "bg-rose-400";
  return (
    <div className="flex items-center gap-2.5">
      <div className="flex-1 rounded-full bg-slate-100 h-1.5">
        <div className={`h-1.5 rounded-full transition-all ${color}`} style={{ width: `${score}%` }} />
      </div>
      <span className={`text-xs font-bold tabular-nums ${score >= 70 ? "text-emerald-600" : score >= 40 ? "text-amber-600" : "text-rose-500"}`}>
        {score}%
      </span>
    </div>
  );
}

export default function JobDetailPage() {
  const { requirementId } = useParams<{ requirementId: string }>();
  const router = useRouter();
  const [job, setJob]             = useState<Job | null>(null);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState("");
  const [statusOpen, setStatusOpen]     = useState(false);
  const [savingStatus, setSavingStatus] = useState(false);

  // Candidate scanner state
  const [scanning, setScanning]       = useState(false);
  const [scanResult, setScanResult]   = useState<ScanResult | null>(null);
  const [scanError, setScanError]     = useState("");
  const [scanned, setScanned]         = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [importSuccess, setImportSuccess] = useState(false);
  
  const [importedCandidates, setImportedCandidates] = useState<MatchedCandidate[]>([]);
  
  // Pipeline state
  const [runningPipeline, setRunningPipeline] = useState(false);
  const [pipelineSuccessMessage, setPipelineSuccessMessage] = useState("");
  
  // Filter state
  const [filterDecision, setFilterDecision] = useState<string>("");
  const [filterScoreBand, setFilterScoreBand] = useState<string>("");
  const [filterFreshness, setFilterFreshness] = useState<string>("");
  const [filterAgentStatus, setFilterAgentStatus] = useState<string>("");
  const [showFilters, setShowFilters] = useState(false);
  const hasFilters = Boolean(filterDecision || filterScoreBand || filterFreshness || filterAgentStatus);

  const loadImported = useCallback(async () => {
    try {
      const params = filterAgentStatus ? { agent_status: filterAgentStatus } : {};
      const res = await apiClient.get(`/jobs/${requirementId}/imported-candidates`, { params });
      setImportedCandidates(res.data.candidates || []);
    } catch { /* ignore error */ }
  }, [requirementId, filterAgentStatus]);

  useEffect(() => {
    (async () => {
      try {
        const res = await apiClient.get(`/jobs/${requirementId}`);
        setJob(res.data);
      } catch {
        setError("Job not found or you don't have access.");
      } finally {
        setLoading(false);
      }
    })();
    
    const cached = sessionStorage.getItem(`scanResult_${requirementId}`);
    if (cached) {
      try {
        setScanResult(JSON.parse(cached));
        setScanned(true);
      } catch { /* ignore parse error */ }
    }
  }, [requirementId]);

  useEffect(() => {
    loadImported();
  }, [loadImported]);

  async function changeStatus(s: string) {
    if (!job || s === job.status) { setStatusOpen(false); return; }
    setSavingStatus(true);
    try {
      await apiClient.patch(`/jobs/${job.job_id}/status`, { status: s });
      setJob(prev => prev ? { ...prev, status: s } : prev);
    } catch { /* keep */ }
    finally { setSavingStatus(false); setStatusOpen(false); }
  }

  async function runScan() {
    if (!job) return;
    setScanning(true); setScanError(""); setScanResult(null);
    try {
      const res = await apiClient.get(`/jobs/${job.job_id}/matching-candidates`, { params: { limit: 500 } });
      setScanResult(res.data);
      sessionStorage.setItem(`scanResult_${requirementId}`, JSON.stringify(res.data));
      setScanned(true);
      setImportSuccess(false);
    } catch (err: any) {
      setScanError(err.message || "Failed to scan candidates.");
    } finally {
      setScanning(false);
    }
  }

  async function importMatches() {
    if (!scanResult) return;
    setIsImporting(true);
    setScanError("");
    setImportSuccess(false);
    try {
      const res = await apiClient.post(`/jobs/${requirementId}/source-candidates`, {
        limit: 500
      });
      if (res.data.status === "success") {
        setImportSuccess(true);
        sessionStorage.removeItem(`scanResult_${requirementId}`);
        setJob(prev => prev ? { ...prev, total_applications: prev.total_applications + res.data.imported } : null);
      }
    } catch (err: any) {
      setScanError(err.message || "Failed to import candidates.");
    } finally {
      setIsImporting(false);
    }
  }

  async function runPipeline() {
    if (!job) return;
    setRunningPipeline(true);
    setPipelineSuccessMessage("");
    setScanError("");
    try {
      const res = await apiClient.post(`/admin/jobs/${job.job_id}/batch-agent-schedule`);
      setPipelineSuccessMessage(res.data.message);
      // Refetch imported candidates to get updated agent_status
      const importedRes = await apiClient.get(`/jobs/${requirementId}/imported-candidates`);
      setImportedCandidates(importedRes.data.candidates || []);
    } catch (err: any) {
      setScanError(err.message || "Failed to run pipeline.");
    } finally {
      setRunningPipeline(false);
    }
  }

  if (loading) return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-slate-300" />
    </div>
  );

  if (error || !job) return (
    <div className="mx-auto max-w-2xl py-20 text-center">
      <p className="text-slate-500">{error || "Job not found."}</p>
      <button onClick={() => router.push("/job-posts")} className="button-secondary mt-4">
        <ArrowLeft className="h-4 w-4" /> Back to Job Posts
      </button>
    </div>
  );

  const salaryStr = fmtSalary(job.salary_min) && fmtSalary(job.salary_max)
    ? `${fmtSalary(job.salary_min)} – ${fmtSalary(job.salary_max)}`
    : fmtSalary(job.salary_min) ?? fmtSalary(job.salary_max) ?? null;

  const expStr = job.experience_min != null && job.experience_max != null
    ? `${job.experience_min} – ${job.experience_max} yrs`
    : job.experience_min != null ? `${job.experience_min}+ yrs`
    : job.experience_max != null ? `Up to ${job.experience_max} yrs`
    : null;

  const combinedCandidates = [...(scanResult?.candidates || []), ...importedCandidates];
  const filteredCandidates = combinedCandidates.filter(c => {
    if (filterDecision && c.decision !== filterDecision) return false;
    if (filterFreshness && c.freshness !== filterFreshness) return false;
    if (filterScoreBand === ">=70" && c.match_score < 70) return false;
    if (filterScoreBand === "40-69" && (c.match_score < 40 || c.match_score >= 70)) return false;
    return true;
  });

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Back nav */}
      <button onClick={() => router.push("/job-posts")}
        className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 transition">
        <ArrowLeft className="h-4 w-4" /> Back to Job Posts
      </button>

      {/* Header card */}
      <div className="card card-body">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="page-title flex items-center gap-2">
              <Briefcase className="h-5 w-5 text-brand-600 flex-shrink-0" /> {job.title}
            </h1>
            <p className="mt-1 text-sm text-slate-500">{job.department}</p>
          </div>
          <div className="flex items-center gap-3 flex-shrink-0 flex-wrap">
            <div className="relative">
              <button
                onClick={() => setStatusOpen(o => !o)}
                disabled={savingStatus}
                className={`${STATUS_BADGE[job.status] ?? "badge-slate"} inline-flex items-center gap-1.5 cursor-pointer`}>
                {savingStatus ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : job.status.charAt(0).toUpperCase() + job.status.slice(1)}
                <ChevronDown className="h-3.5 w-3.5" />
              </button>
              {statusOpen && (
                <div className="absolute right-0 top-full z-20 mt-1 min-w-[130px] rounded-2xl border border-slate-200 bg-white shadow-card-lg py-1.5">
                  {STATUSES.map(s => (
                    <button key={s} onClick={() => changeStatus(s)}
                      className={`flex w-full items-center gap-2.5 px-3.5 py-2 text-sm font-medium hover:bg-slate-50 ${s === job.status ? "text-brand-600" : "text-slate-700"}`}>
                      <span className={`h-2 w-2 rounded-full ${
                        s === "open" ? "bg-emerald-500" : s === "draft" ? "bg-purple-500" : s === "paused" ? "bg-amber-500" : "bg-slate-400"
                      }`} />
                      {s.charAt(0).toUpperCase() + s.slice(1)}
                    </button>
                  ))}
                </div>
              )}
            </div>
            <button onClick={runScan} disabled={scanning || job.status !== 'open'}
              className="button-primary">
              {scanning
                ? <><Loader2 className="h-4 w-4 animate-spin" /> Scanning…</>
                : <><ScanSearch className="h-4 w-4" /> {job.total_applications > 0 ? "Re-scan for New Candidates" : (scanned ? "Re-scan Candidates" : "Scan Candidates")}</>}
            </button>
          </div>
        </div>

        {/* Meta row */}
        <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-sm text-slate-600">
          {job.location && (
            <span className="flex items-center gap-1.5"><MapPin className="h-4 w-4 text-slate-400" />{job.location}</span>
          )}
          {job.employment_type && (
            <span className="flex items-center gap-1.5"><Clock className="h-4 w-4 text-slate-400" />{job.employment_type}</span>
          )}
          {expStr && (
            <span className="flex items-center gap-1.5"><TrendingUp className="h-4 w-4 text-slate-400" />{expStr}</span>
          )}
          {salaryStr && (
            <span className="flex items-center gap-1.5"><DollarSign className="h-4 w-4 text-slate-400" />{salaryStr}</span>
          )}
          <span className="flex items-center gap-1.5">
            <Users className="h-4 w-4 text-slate-400" />
            {job.total_applications} application{job.total_applications !== 1 ? "s" : ""}
          </span>
        </div>
      </div>

      {/* Description */}
      <div className="card card-body">
        <h2 className="section-label mb-3">Job Description</h2>
        <div className="text-sm leading-relaxed text-slate-700 whitespace-pre-wrap">
          {job.description || "No description provided."}
        </div>
      </div>

      {/* Skills grid */}
      <div className="grid gap-4 sm:grid-cols-2">
        {job.skills_required.length > 0 && (
          <div className="card card-body">
            <h2 className="section-label mb-3 flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> Required Skills
            </h2>
            <div className="flex flex-wrap gap-2">
              {job.skills_required.map(s => (
                <span key={s} className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">{s.trim()}</span>
              ))}
            </div>
          </div>
        )}
        {job.preferred_skills.length > 0 && (
          <div className="card card-body">
            <h2 className="section-label mb-3">Preferred Skills</h2>
            <div className="flex flex-wrap gap-2">
              {job.preferred_skills.map(s => (
                <span key={s} className="rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700">{s.trim()}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Education & Certifications */}
      {(job.education_requirements || job.mandatory_certifications.length > 0) && (
        <div className="card card-body space-y-4">
          {job.education_requirements && (
            <div>
              <h2 className="section-label mb-2 flex items-center gap-1.5">
                <GraduationCap className="h-3.5 w-3.5 text-slate-500" /> Education
              </h2>
              <p className="text-sm text-slate-700">{job.education_requirements}</p>
            </div>
          )}
          {job.mandatory_certifications.length > 0 && (
            <div>
              <h2 className="section-label mb-2 flex items-center gap-1.5">
                <Award className="h-3.5 w-3.5 text-amber-500" /> Mandatory Certifications
              </h2>
              <div className="flex flex-wrap gap-2">
                {job.mandatory_certifications.map(c => (
                  <span key={c} className="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">{c.trim()}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Screening thresholds */}
      {(job.screening_pass_score != null || job.screening_review_score != null) && (
        <div className="card card-body">
          <h2 className="section-label mb-3">Screening Thresholds</h2>
          <div className="flex gap-8 text-sm text-slate-700">
            {job.screening_pass_score != null && (
              <div>
                <p className="text-xs text-slate-400 mb-1">Auto-pass score</p>
                <p className="text-xl font-bold text-emerald-600">{job.screening_pass_score}</p>
              </div>
            )}
            {job.screening_review_score != null && (
              <div>
                <p className="text-xs text-slate-400 mb-1">Manual review score</p>
                <p className="text-xl font-bold text-amber-600">{job.screening_review_score}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Candidate Scan Results ─────────────────────────────── */}
      {scanError && (
        <div className="card card-body flex items-center gap-3 border-red-200 bg-red-50">
          <XCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
          <p className="text-sm text-red-700">{scanError}</p>
        </div>
      )}

      {importSuccess && (
        <div className="card card-body flex items-center gap-3 border-emerald-200 bg-emerald-50">
          <CheckCircle2 className="h-5 w-5 text-emerald-500 flex-shrink-0" />
          <p className="text-sm text-emerald-700">Successfully imported candidates to the pipeline!</p>
        </div>
      )}

      {pipelineSuccessMessage && (
        <div className="card card-body flex items-center gap-3 border-emerald-200 bg-emerald-50 animate-fade-in">
          <CheckCircle2 className="h-5 w-5 text-emerald-500 flex-shrink-0" />
          <p className="text-sm text-emerald-700">{pipelineSuccessMessage}</p>
        </div>
      )}

      {(scanResult || importedCandidates.length > 0) && (
        <div className="card overflow-hidden animate-fade-in">
          <div className="card-header flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Zap className="h-4 w-4 text-amber-500" /> Matching Candidates from Pool
                </h2>
                <p className="mt-0.5 text-xs text-slate-500">
                  {combinedCandidates.length} candidate{combinedCandidates.length !== 1 ? "s" : ""} matched
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => setShowFilters(!showFilters)}
                  className={`button-secondary py-1.5 px-3 text-xs ${hasFilters ? "ring-2 ring-brand-400" : ""}`}>
                  <SlidersHorizontal className="h-3.5 w-3.5" /> Filters
                  {hasFilters && <span className="ml-1 rounded-full bg-brand-600 px-1.5 py-0.5 text-2xs text-white">ON</span>}
                </button>
                {scanResult && scanResult.candidates.length > 0 && !importSuccess && (
                  <button onClick={importMatches} disabled={isImporting} className="button-primary py-1.5 px-3 text-xs">
                    {isImporting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />}
                    {isImporting ? "Importing..." : "Import Matches to Pipeline"}
                  </button>
                )}
                {importedCandidates.some(c => c.application_status === "R1_READY") && (
                  <button onClick={runPipeline} disabled={runningPipeline} className="button-primary py-1.5 px-3 text-xs bg-emerald-600 hover:bg-emerald-700 shadow-emerald-600/20 border-transparent">
                    {runningPipeline ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Zap className="h-3.5 w-3.5 fill-white" />}
                    {runningPipeline ? "Running..." : "Run Pipeline"}
                  </button>
                )}
              </div>
            </div>
            
            {showFilters && (
              <div className="flex flex-wrap gap-4 items-end bg-slate-50/50 p-3 rounded-lg border border-slate-100 animate-fade-in mt-4">
                <div className="space-y-1 min-w-[140px]">
                  <label className="text-xs font-semibold text-slate-600 flex items-center gap-1"><Filter className="h-3 w-3" /> Decision</label>
                  <select className="input text-sm py-1.5" value={filterDecision} onChange={e => setFilterDecision(e.target.value)}>
                    <option value="">All</option>
                    <option value="PASS">PASS</option>
                    <option value="REVIEW">REVIEW</option>
                  </select>
                </div>
                <div className="space-y-1 min-w-[140px]">
                  <label className="text-xs font-semibold text-slate-600">Score Band</label>
                  <select className="input text-sm py-1.5" value={filterScoreBand} onChange={e => setFilterScoreBand(e.target.value)}>
                    <option value="">All</option>
                    <option value=">=70">≥70% match</option>
                    <option value="40-69">40–69% match</option>
                  </select>
                </div>
                <div className="space-y-1 min-w-[140px]">
                  <label className="text-xs font-semibold text-slate-600">Freshness</label>
                  <select className="input text-sm py-1.5" value={filterFreshness} onChange={e => setFilterFreshness(e.target.value)}>
                    <option value="">All</option>
                    <option value="FRESH">Fresh</option>
                    <option value="STALE">Stale</option>
                    <option value="AGED">Aged</option>
                  </select>
                </div>
                <div className="space-y-1 min-w-[140px]">
                  <label className="text-xs font-semibold text-slate-600">R1 Interview</label>
                  <select className="input text-sm py-1.5" value={filterAgentStatus} onChange={e => setFilterAgentStatus(e.target.value)}>
                    <option value="">All</option>
                    <option value="Scheduled">Scheduled</option>
                    <option value="Completed">Completed</option>
                  </select>
                </div>
                {hasFilters && (
                  <button onClick={() => { setFilterDecision(""); setFilterScoreBand(""); setFilterFreshness(""); setFilterAgentStatus(""); }} className="button-secondary text-xs h-fit py-1.5">
                    <X className="h-3.5 w-3.5" /> Clear
                  </button>
                )}
              </div>
            )}
          </div>

          {filteredCandidates.length === 0 ? (
            <div className="py-16 text-center">
              <User className="mx-auto mb-3 h-10 w-10 text-slate-200" />
              <p className="text-sm font-medium text-slate-500">No candidates match your criteria.</p>
              <p className="mt-1 text-xs text-slate-400">Try adjusting your filters or running a new scan.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Candidate</th>
                    <th>Location</th>
                    <th>Experience</th>
                    <th>Freshness</th>
                    <th>Matched Skills</th>
                    <th>Missing Skills</th>
                    <th className="w-32">Match Score</th>
                    <th>Validator Decision</th>
                    <th>HR Action</th>
                    <th>Status</th>
                    <th>R1 Interview</th>
                    <th>R1 Result</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCandidates.map(c => (
                    <tr key={c.candidate_id} className={c.is_imported ? "bg-slate-50/50" : ""}>
                      <td>
                        <div className="font-semibold text-slate-800 flex items-center gap-1.5">
                          {c.name}
                        </div>
                        {c.phone && <div className="text-xs text-slate-400">{c.phone}</div>}
                      </td>
                      <td className="text-slate-600">
                        {[c.city, c.state].filter(Boolean).join(", ") || "—"}
                      </td>
                      <td className="text-slate-600">
                        {c.experience_years != null ? `${c.experience_years.toFixed(1)} yrs` : "—"}
                      </td>
                      <td>
                        <span className={FRESHNESS_BADGE[c.freshness] ?? "badge-slate"}>
                          {c.freshness || "—"}
                        </span>
                      </td>
                      <td>
                        <div className="flex flex-wrap gap-1">
                          {c.matched_skills.length > 0
                            ? c.matched_skills.slice(0, 4).map(s => (
                                <span key={s} className="rounded-full bg-emerald-50 px-2 py-0.5 text-2xs font-semibold text-emerald-700">{s}</span>
                              ))
                            : <span className="text-xs text-slate-400">—</span>}
                          {c.matched_skills.length > 4 && (
                            <span className="text-2xs text-slate-400">+{c.matched_skills.length - 4}</span>
                          )}
                        </div>
                      </td>
                      <td>
                        <div className="flex flex-wrap gap-1">
                          {c.missing_skills.length > 0
                            ? c.missing_skills.slice(0, 3).map(s => (
                                <span key={s} className="rounded-full bg-rose-50 px-2 py-0.5 text-2xs font-semibold text-rose-600">{s}</span>
                              ))
                            : <span className="text-2xs text-emerald-600 font-semibold">All matched</span>}
                          {c.missing_skills.length > 3 && (
                            <span className="text-2xs text-slate-400">+{c.missing_skills.length - 3}</span>
                          )}
                        </div>
                      </td>
                      <td>
                        <MatchBar score={c.match_score} />
                      </td>
                      <td>
                        <span className={c.decision === "PASS" ? "text-emerald-600 font-medium text-xs" : c.decision === "REVIEW" ? "text-amber-600 font-medium text-xs" : "text-red-600 font-medium text-xs"}>
                          {c.decision}
                        </span>
                      </td>
                      <td>
                        {c.is_imported && c.application_id ? (
                          <HrActionCell appId={c.application_id} currentAction={c.hr_action || null} onRefresh={loadImported} />
                        ) : (
                          <span className="text-xs text-slate-400">—</span>
                        )}
                      </td>
                      <td>
                        {c.is_imported && c.application_id ? (
                          <span className="badge-slate">
                            {(c.application_status === "R1_READY" || c.application_status?.toLowerCase() === "shortlisted") ? "R1 Ready" : (c.application_status || "—")}
                          </span>
                        ) : (
                          <span className="text-xs text-slate-400">—</span>
                        )}
                      </td>
                      <td>
                        {c.is_imported && c.application_id && (c.application_status === "R1_READY" || c.application_status?.toLowerCase() === "shortlisted") ? (
                          <ScheduleAgentInterviewButton appId={c.application_id} />
                        ) : (
                          <span className="text-xs text-slate-400">—</span>
                        )}
                      </td>
                      <td>
                        {c.is_imported && c.application_id && (c.application_status === "R1_READY" || c.application_status?.toLowerCase() === "shortlisted") ? (
                          <a href={`/applications/${c.application_id}/r1-results`} className="text-xs font-semibold text-brand-600 hover:text-brand-700 hover:underline inline-flex items-center gap-1">
                            View Result
                          </a>
                        ) : (
                          <span className="text-xs text-slate-400">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Prompt to scan if not yet done */}
      {!scanned && !scanning && (
        <div className="card card-body flex flex-col items-center gap-4 py-10 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-50">
            <ScanSearch className="h-7 w-7 text-brand-600" />
          </div>
          <div>
            <p className="text-base font-semibold text-slate-800">Find matching candidates</p>
            <p className="mt-1 text-sm text-slate-500 max-w-sm">
              Scan the talent pool for candidates who match this job's skills and experience criteria.
            </p>
          </div>
          <button onClick={runScan} disabled={scanning || job.status !== 'open'} className="button-primary">
            <ScanSearch className="h-4 w-4" /> Scan Candidates Now
          </button>
        </div>
      )}
    </div>
  );
}

function ScheduleAgentInterviewButton({ appId }: { appId: string }) {
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<string>("none");
  const [webCallUrl, setWebCallUrl] = useState<string | null>(null);
  const [agentData, setAgentData] = useState<any>(null);

  useEffect(() => {
    checkStatus();
    let interval: NodeJS.Timeout;
    if (["queued", "ringing", "in-progress"].includes(status)) {
      interval = setInterval(checkStatus, 5000);
    }
    return () => clearInterval(interval);
  }, [appId, status]);

  async function checkStatus() {
    try {
      const res = await apiClient.get(`/admin/candidates/${appId}/agent-status`);
      const data = res.data;
      if (data.status !== "none") {
        setStatus(data.status);
        setWebCallUrl(data.web_call_url);
        if (data.status === "ended") setAgentData(data);
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
      const res = await apiClient.post(`/admin/candidates/${appId}/agent-schedule`);
      setStatus("queued");
      setWebCallUrl(res.data.web_call_url);
      setAgentData(null);
    } catch (err: any) {
      alert("Failed to schedule R1 interview: " + (err?.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div className="h-7 flex items-center justify-center"><Loader2 className="h-4 w-4 animate-spin text-slate-400" /></div>;

  if (status === "ended" && agentData) {
    return (
      <div className="button-primary text-xs h-7 px-3 bg-emerald-600 text-white border-transparent whitespace-nowrap shadow-sm shadow-emerald-600/20 cursor-default inline-flex items-center gap-1.5 hover:bg-emerald-600">
        <Check className="h-4 w-4" /> Completed
      </div>
    );
  }

  if (!["none", "ended", "error", "failed", "canceled"].includes(status)) {
    return (
      <div className="flex flex-col gap-1 items-start">
        <span className="inline-flex items-center gap-1 text-[10px] font-medium text-amber-600 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
          <Loader2 className="h-3 w-3 animate-spin" /> {status.charAt(0).toUpperCase() + status.slice(1).replace("-", " ")}
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
      Schedule Interview
    </button>
  );
}
