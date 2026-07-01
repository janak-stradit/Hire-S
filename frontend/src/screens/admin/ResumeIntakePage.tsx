"use client";

import {
  Upload, FileText, X, ChevronDown, ChevronUp, CheckCircle2,
  RefreshCw, AlertCircle, Info, Loader2
} from "lucide-react";
import { useCallback, useRef, useState } from "react";
import { apiClient } from "../../api/client";

type WorkEntryOut = { role: string; company: string; duration: string };
type ParsedField = {
  name: string | null;
  email: string | null;
  phone: string | null;
  city: string | null;
  state: string | null;
  current_company: string | null;
  current_role: string | null;
  total_experience: number | null;
  expected_salary: number | null;
  notice_period: string | null;
  highest_education: string | null;
  skills: string[];
  work_history: WorkEntryOut[];
};
type UploadResult = {
  filename: string;
  action: "created" | "updated" | "skipped" | "error";
  candidate_id: string | null;
  parsed: ParsedField | null;
  error: string | null;
};
type BulkResponse = { results: UploadResult[]; total: number; created: number; updated: number; skipped: number; errors: number };

const ACTION_BADGE: Record<string, string> = {
  created: "badge-green",
  updated: "badge-blue",
  skipped: "badge-yellow",
  error:   "badge-red",
};

const DOTS = ["bg-brand-500", "bg-sky-500", "bg-emerald-500", "bg-amber-500", "bg-purple-500", "bg-rose-500", "bg-teal-500", "bg-orange-500"];

function ResultRow({ result }: { result: UploadResult }) {
  const [open, setOpen] = useState(false);
  const p = result.parsed;
  const missingFields = p ? (["name","email","phone","current_role","current_company","total_experience","skills"] as const)
    .filter(k => {
      const v = p[k];
      if (Array.isArray(v)) return v.length === 0;
      return v == null || v === "";
    }) : [];

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-card-sm overflow-hidden">
      <button onClick={() => setOpen(o => !o)}
        className="flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-slate-50 transition">
        <span className={`${ACTION_BADGE[result.action]} min-w-[72px] text-center`}>{result.action}</span>
        <span className="flex-1 truncate text-sm font-medium text-slate-700">{result.filename}</span>
        {p?.name && <span className="text-xs text-slate-400">{p.name}</span>}
        {result.error && <span className="text-xs text-red-500 truncate max-w-[200px]">{result.error}</span>}
        {open ? <ChevronUp className="h-4 w-4 text-slate-400 flex-shrink-0" /> : <ChevronDown className="h-4 w-4 text-slate-400 flex-shrink-0" />}
      </button>

      {open && p && (
        <div className="border-t border-slate-100 px-4 py-4 space-y-4 animate-fade-in">
          {missingFields.length > 0 && (
            <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2.5">
              <AlertCircle className="h-4 w-4 text-amber-500 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-amber-700">Missing fields: <span className="font-semibold">{missingFields.join(", ")}</span></p>
            </div>
          )}
          <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs sm:grid-cols-3">
            {([
              ["Name",        p.name],
              ["Email",       p.email],
              ["Phone",       p.phone],
              ["City",        p.city],
              ["State",       p.state],
              ["Role",        p.current_role],
              ["Company",     p.current_company],
              ["Experience",  p.total_experience != null ? `${p.total_experience} yrs` : null],
              ["Salary",      p.expected_salary  != null ? `₹${(p.expected_salary/100000).toFixed(1)} L` : null],
              ["Notice",      p.notice_period],
              ["Education",   p.highest_education],
            ] as [string, string | null][]).filter(([, v]) => v).map(([l, v]) => (
              <div key={l}>
                <p className="text-2xs font-semibold uppercase tracking-wider text-slate-400">{l}</p>
                <p className="mt-0.5 font-medium text-slate-700">{v}</p>
              </div>
            ))}
          </div>

          {p.skills.length > 0 && (
            <div>
              <p className="text-2xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Skills</p>
              <div className="flex flex-wrap gap-1.5">
                {p.skills.map(s => (
                  <span key={s} className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-2xs font-medium text-slate-700">{s}</span>
                ))}
              </div>
            </div>
          )}

          {p.work_history.length > 0 && (
            <div>
              <p className="text-2xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Work History</p>
              <div className="relative space-y-3 pl-4">
                <div className="absolute inset-y-0 left-1.5 w-px bg-slate-100" />
                {p.work_history.map((w, i) => (
                  <div key={i} className="relative">
                    <div className={`absolute -left-[11px] top-1 h-2.5 w-2.5 rounded-full border-2 border-white ${DOTS[i % DOTS.length]}`} />
                    <p className="text-xs font-semibold text-slate-800">{w.role}</p>
                    <p className="text-2xs text-slate-500">{w.company}</p>
                    {w.duration && <p className="text-2xs text-slate-400">{w.duration}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ResumeIntakePage() {
  const inputRef  = useRef<HTMLInputElement>(null);
  const [files, setFiles]     = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<BulkResponse | null>(null);
  const [activeFilter, setActiveFilter] = useState<string>("all");
  const [dragging, setDragging] = useState(false);

  function addFiles(incoming: FileList | null) {
    if (!incoming) return;
    const pdfs = Array.from(incoming).filter(f => f.type === "application/pdf" || f.name.endsWith(".pdf"));
    setFiles(prev => {
      const existing = new Set(prev.map(f => f.name));
      return [...prev, ...pdfs.filter(f => !existing.has(f.name))];
    });
  }

  function removeFile(name: string) { setFiles(prev => prev.filter(f => f.name !== name)); }

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDragging(false);
    addFiles(e.dataTransfer.files);
  }, []);

  async function upload() {
    if (!files.length) return;
    setLoading(true); setResponse(null);
    try {
      const form = new FormData();
      files.forEach(f => form.append("files", f));
      const res = await apiClient.post<BulkResponse>("/resume-intake/upload", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResponse(res.data);
      setFiles([]);
    } catch {
      // show partial error
    } finally {
      setLoading(false);
    }
  }

  const summaryCards = response ? [
    { label: "Created",  value: response.created,  key: "created",  color: "text-emerald-600", border: "border-emerald-200", bg: "bg-emerald-50" },
    { label: "Updated",  value: response.updated,  key: "updated",  color: "text-brand-600",   border: "border-blue-200",    bg: "bg-blue-50"    },
    { label: "Skipped",  value: response.skipped,  key: "skipped",  color: "text-amber-600",   border: "border-amber-200",   bg: "bg-amber-50"   },
    { label: "Errors",   value: response.errors,   key: "error",    color: "text-red-600",     border: "border-red-200",     bg: "bg-red-50"     },
  ] : [];

  const filtered = response?.results.filter(r => activeFilter === "all" || r.action === activeFilter) ?? [];

  return (
    <div className="mx-auto max-w-[860px] space-y-5">
      <div>
        <h1 className="page-title flex items-center gap-2"><Upload className="h-5 w-5 text-brand-600" /> Resume Intake</h1>
        <p className="page-subtitle mt-0.5">Upload PDF resumes to parse and add candidates to the talent pool.</p>
      </div>

      {/* How-to tip */}
      <div className="flex items-start gap-3 rounded-xl border border-brand-100 bg-brand-50 px-4 py-3">
        <Info className="h-4 w-4 text-brand-500 flex-shrink-0 mt-0.5" />
        <p className="text-xs text-brand-700 leading-relaxed">
          Upload one or more PDF resumes. If a resume matches an existing candidate (by email or phone), the record will be updated — not duplicated. Extraction uses AI-assisted parsing; review missing fields after upload.
        </p>
      </div>

      {/* Drop zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={`relative flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-12 text-center transition ${dragging ? "border-brand-400 bg-brand-50" : "border-slate-200 bg-white hover:border-brand-300 hover:bg-slate-50"}`}
      >
        <input ref={inputRef} type="file" multiple accept=".pdf,application/pdf" className="hidden"
          onChange={e => addFiles(e.target.files)} />
        <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-50 ring-1 ring-brand-200">
          <Upload className="h-7 w-7 text-brand-600" />
        </div>
        <p className="text-sm font-semibold text-slate-700">Drop PDF resumes here or click to browse</p>
        <p className="mt-1 text-xs text-slate-400">Supports multiple files · PDF only</p>
      </div>

      {/* Queue */}
      {files.length > 0 && (
        <div className="card overflow-hidden">
          <div className="card-header flex items-center justify-between">
            <p className="text-xs font-semibold text-slate-600">{files.length} file{files.length > 1 ? "s" : ""} queued</p>
            <button onClick={() => setFiles([])} className="text-xs text-slate-400 hover:text-red-500 transition">Clear all</button>
          </div>
          <div className="max-h-[280px] overflow-y-auto divide-y divide-slate-50">
            {files.map(f => (
              <div key={f.name} className="flex items-center gap-3 px-4 py-2.5">
                <FileText className="h-4 w-4 flex-shrink-0 text-slate-400" />
                <p className="flex-1 truncate text-xs text-slate-700">{f.name}</p>
                <p className="text-2xs text-slate-400 flex-shrink-0">{(f.size / 1024).toFixed(0)} KB</p>
                <button onClick={() => removeFile(f.name)} className="text-slate-300 hover:text-red-500 transition">
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
          </div>
          <div className="border-t border-slate-100 px-4 py-3">
            <button onClick={upload} disabled={loading} className="button-primary w-full justify-center">
              {loading ? <><Loader2 className="h-4 w-4 animate-spin" /> Processing resumes…</> : <><Upload className="h-4 w-4" /> Upload & Parse {files.length} Resume{files.length > 1 ? "s" : ""}</>}
            </button>
          </div>
        </div>
      )}

      {/* Results */}
      {response && (
        <div className="space-y-4 animate-fade-in">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-slate-700">
              Processed {response.total} resume{response.total !== 1 ? "s" : ""}
            </p>
            <button onClick={() => { setResponse(null); setActiveFilter("all"); }} className="button-secondary text-xs">
              <RefreshCw className="h-3.5 w-3.5" /> Upload More
            </button>
          </div>

          {/* Summary cards (doubles as filters) */}
          <div className="grid grid-cols-4 gap-3">
            {summaryCards.map(({ label, value, key, color, border, bg }) => (
              <button key={key} onClick={() => setActiveFilter(activeFilter === key ? "all" : key)}
                className={`stat-card text-left border transition ${activeFilter === key ? `${border} ${bg} ring-2 ring-offset-1 ring-${color.replace("text-","")}/40` : ""}`}>
                <span className="stat-label">{label}</span>
                <span className={`stat-value ${color}`}>{value}</span>
              </button>
            ))}
          </div>

          {/* Individual results */}
          <div className="space-y-2">
            {filtered.map((r, i) => <ResultRow key={i} result={r} />)}
            {filtered.length === 0 && (
              <div className="text-center py-10 text-sm text-slate-400">
                <CheckCircle2 className="mx-auto mb-2 h-8 w-8 text-slate-200" />
                No results for this filter
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
