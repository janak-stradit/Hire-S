"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  ArrowLeft, Briefcase, MapPin, Clock, DollarSign, GraduationCap,
  Award, Users, CheckCircle2, Loader2, ChevronDown,
  ScanSearch, User, Zap, XCircle, TrendingUp, Download
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
            <button onClick={runScan} disabled={scanning}
              className="button-primary">
              {scanning
                ? <><Loader2 className="h-4 w-4 animate-spin" /> Scanning…</>
                : <><ScanSearch className="h-4 w-4" /> {scanned ? "Re-scan Candidates" : "Scan Candidates"}</>}
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

      {scanResult && (
        <div className="card overflow-hidden animate-fade-in">
          <div className="card-header flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Zap className="h-4 w-4 text-amber-500" /> Matching Candidates from Pool
              </h2>
              <p className="mt-0.5 text-xs text-slate-500">
                {scanResult.total_matches} candidate{scanResult.total_matches !== 1 ? "s" : ""} matched
                {scanResult.candidates.length < scanResult.total_matches && ` · showing top ${scanResult.candidates.length}`}
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3 text-xs text-slate-500">
                <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-emerald-500" /> ≥70% match</span>
                <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-amber-400" /> 40–69%</span>
                <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-rose-400" /> &lt;40%</span>
              </div>
              {scanResult.candidates.length > 0 && !importSuccess && (
                <button onClick={importMatches} disabled={isImporting} className="button-primary py-1.5 px-3 text-xs">
                  {isImporting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />}
                  {isImporting ? "Importing..." : "Import Matches to Pipeline"}
                </button>
              )}
            </div>
          </div>

          {scanResult.candidates.length === 0 ? (
            <div className="py-16 text-center">
              <User className="mx-auto mb-3 h-10 w-10 text-slate-200" />
              <p className="text-sm font-medium text-slate-500">No reusable candidates match this job's criteria.</p>
              <p className="mt-1 text-xs text-slate-400">Try uploading more resumes or adjusting the experience range.</p>
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
                  </tr>
                </thead>
                <tbody>
                  {scanResult.candidates.map(c => (
                    <tr key={c.candidate_id}>
                      <td>
                        <div className="font-semibold text-slate-800">{c.name}</div>
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
          <button onClick={runScan} className="button-primary">
            <ScanSearch className="h-4 w-4" /> Scan Candidates Now
          </button>
        </div>
      )}
    </div>
  );
}
