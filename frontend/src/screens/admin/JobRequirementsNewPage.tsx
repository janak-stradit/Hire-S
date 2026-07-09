"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Briefcase, Upload, Loader2, CheckCircle2, FileText, Plus, X
} from "lucide-react";
import { apiClient } from "../../api/client";

type Tab = "form" | "excel";

const EMPLOYMENT_TYPES = ["Full-time", "Part-time", "Contract", "Internship", "Freelance"];
const WORK_MODES       = ["Hybrid", "Remote", "On-site"];
const STATUSES         = ["draft", "open"];

function TagInput({ label, value, onChange }: { label: string; value: string[]; onChange: (v: string[]) => void }) {
  const [input, setInput] = useState("");
  function add() {
    const trimmed = input.trim();
    if (trimmed && !value.includes(trimmed)) onChange([...value, trimmed]);
    setInput("");
  }
  return (
    <div className="space-y-1">
      <label className="block text-xs font-semibold text-slate-600">{label}</label>
      <div className="flex flex-wrap gap-1.5 rounded-lg border border-slate-200 bg-white p-2 min-h-[42px]">
        {value.map(s => (
          <span key={s} className="inline-flex items-center gap-1 rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-medium text-brand-700">
            {s}
            <button type="button" onClick={() => onChange(value.filter(x => x !== s))} className="text-brand-400 hover:text-brand-700">
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
        <input
          className="flex-1 min-w-[120px] text-sm outline-none placeholder:text-slate-400 bg-transparent"
          placeholder="Type and press Enter or comma…"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === "Enter" || e.key === ",") { e.preventDefault(); add(); } }}
          onBlur={add}
        />
      </div>
    </div>
  );
}

function JobForm() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError]     = useState("");

  const [form, setForm] = useState({
    title: "", department: "", location: "",
    employment_type: "Full-time", work_mode: "Hybrid",
    experience_min: "", experience_max: "",
    salary_min: "", salary_max: "",
    description: "", education_requirements: "",
    status: "draft",
    screening_pass_score: "75",
    screening_review_score: "60",
  });
  const [requiredSkills, setRequired]     = useState<string[]>([]);
  const [preferredSkills, setPreferred]   = useState<string[]>([]);
  const [certifications, setCerts]        = useState<string[]>([]);

  function set(field: string, value: string) { setForm(f => ({ ...f, [field]: value })); }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!requiredSkills.length) { setError("At least one required skill is needed."); return; }
    setLoading(true); setError("");
    try {
      await apiClient.post("/jobs/create", {
        title:                   form.title,
        department:              form.department,
        location:                form.location,
        employment_type:         `${form.employment_type} – ${form.work_mode}`,
        experience_min:          form.experience_min ? Number(form.experience_min) : null,
        experience_max:          form.experience_max ? Number(form.experience_max) : null,
        salary_min:              form.salary_min ? Number(form.salary_min) : null,
        salary_max:              form.salary_max ? Number(form.salary_max) : null,
        description:             form.description,
        skills_required:         requiredSkills,
        preferred_skills:        preferredSkills,
        education_requirements:  form.education_requirements,
        mandatory_certifications: certifications,
        status:                  form.status,
        screening_pass_score:    form.screening_pass_score ? Number(form.screening_pass_score) : null,
        screening_review_score:  form.screening_review_score ? Number(form.screening_review_score) : null,
      });
      setSuccess(true);
      setTimeout(() => router.push("/job-posts"), 1500);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(Array.isArray(msg) ? msg.map((m: { msg: string }) => m.msg).join(", ") : (msg || "Failed to create job."));
    } finally { setLoading(false); }
  }

  return (
    <form onSubmit={submit} className="card card-body space-y-5">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1 sm:col-span-2">
          <label className="block text-xs font-semibold text-slate-600">Job Title *</label>
          <input className="input" placeholder="e.g. Senior Backend Engineer" required value={form.title} onChange={e => set("title", e.target.value)} />
        </div>
        <div className="space-y-1">
          <label className="block text-xs font-semibold text-slate-600">Department *</label>
          <input className="input" placeholder="e.g. Engineering" required value={form.department} onChange={e => set("department", e.target.value)} />
        </div>
        <div className="space-y-1">
          <label className="block text-xs font-semibold text-slate-600">Location *</label>
          <input className="input" placeholder="e.g. Pune / Hybrid" required value={form.location} onChange={e => set("location", e.target.value)} />
        </div>
        <div className="space-y-1">
          <label className="block text-xs font-semibold text-slate-600">Employment Type</label>
          <select className="input" value={form.employment_type} onChange={e => set("employment_type", e.target.value)}>
            {EMPLOYMENT_TYPES.map(t => <option key={t}>{t}</option>)}
          </select>
        </div>
        <div className="space-y-1">
          <label className="block text-xs font-semibold text-slate-600">Work Mode</label>
          <select className="input" value={form.work_mode} onChange={e => set("work_mode", e.target.value)}>
            {WORK_MODES.map(m => <option key={m}>{m}</option>)}
          </select>
        </div>
        <div className="space-y-1">
          <label className="block text-xs font-semibold text-slate-600">Experience Min (yrs)</label>
          <input className="input" type="number" min={0} placeholder="0" value={form.experience_min} onChange={e => set("experience_min", e.target.value)} />
        </div>
        <div className="space-y-1">
          <label className="block text-xs font-semibold text-slate-600">Experience Max (yrs)</label>
          <input className="input" type="number" min={0} placeholder="5" value={form.experience_max} onChange={e => set("experience_max", e.target.value)} />
        </div>
        <div className="space-y-1">
          <label className="block text-xs font-semibold text-slate-600">Salary Min (₹ LPA)</label>
          <input className="input" type="number" min={0} placeholder="600000" value={form.salary_min} onChange={e => set("salary_min", e.target.value)} />
        </div>
        <div className="space-y-1">
          <label className="block text-xs font-semibold text-slate-600">Salary Max (₹ LPA)</label>
          <input className="input" type="number" min={0} placeholder="1200000" value={form.salary_max} onChange={e => set("salary_max", e.target.value)} />
        </div>
        <div className="space-y-1 sm:col-span-2">
          <TagInput label="Required Skills *" value={requiredSkills} onChange={setRequired} />
        </div>
        <div className="space-y-1 sm:col-span-2">
          <TagInput label="Preferred Skills" value={preferredSkills} onChange={setPreferred} />
        </div>
        <div className="space-y-1 sm:col-span-2">
          <TagInput label="Mandatory Certifications" value={certifications} onChange={setCerts} />
        </div>
        <div className="space-y-1 sm:col-span-2">
          <label className="block text-xs font-semibold text-slate-600">Education Requirements</label>
          <input className="input" placeholder="e.g. B.E. / B.Tech in CS or equivalent" value={form.education_requirements} onChange={e => set("education_requirements", e.target.value)} />
        </div>
        <div className="space-y-1 sm:col-span-2">
          <label className="block text-xs font-semibold text-slate-600">Job Description *</label>
          <textarea className="input min-h-[140px] resize-y" placeholder="Describe responsibilities, expectations, and required background…" required value={form.description} onChange={e => set("description", e.target.value)} />
        </div>
        <div className="space-y-1">
          <label className="block text-xs font-semibold text-slate-600">Status</label>
          <select className="input" value={form.status} onChange={e => set("status", e.target.value)}>
            {STATUSES.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
          </select>
        </div>
        <div className="space-y-1">
          <label className="block text-xs font-semibold text-slate-600">Auto-Pass Score (%)</label>
          <input className="input" type="number" min={0} max={100} placeholder="75" value={form.screening_pass_score} onChange={e => set("screening_pass_score", e.target.value)} />
        </div>
        <div className="space-y-1">
          <label className="block text-xs font-semibold text-slate-600">Manual Review Score (%)</label>
          <input className="input" type="number" min={0} max={100} placeholder="60" value={form.screening_review_score} onChange={e => set("screening_review_score", e.target.value)} />
        </div>
      </div>

      {error   && <p className="text-sm text-red-600">{error}</p>}
      {success && <div className="flex items-center gap-2 text-sm text-emerald-600"><CheckCircle2 className="h-4 w-4" /> Job created! Redirecting…</div>}

      <div className="flex gap-3">
        <button type="submit" disabled={loading || success} className="button-primary">
          {loading ? <><Loader2 className="h-4 w-4 animate-spin" /> Creating…</> : <><Plus className="h-4 w-4" /> Create Job</>}
        </button>
        <button type="button" onClick={() => window.history.back()} className="button-secondary">Cancel</button>
      </div>
    </form>
  );
}

function ExcelUpload() {
  const router = useRouter();
  const [file, setFile]       = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState<{ created: number; updated: number; failed: number; errors: { row: number; error: string }[] } | null>(null);
  const [error, setError]     = useState("");

  async function handleUpload() {
    if (!file) return;
    setLoading(true); setError(""); setResult(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await apiClient.post("/jobs/from-excel", form, { headers: { "Content-Type": "multipart/form-data" } });
      setResult(res.data);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Upload failed.");
    } finally { setLoading(false); }
  }

  return (
    <div className="card card-body space-y-4">
      <p className="text-sm text-slate-600">
        Upload an Excel or CSV file with job requirements. Each row becomes a job in the database.
        The file must have a sheet named <code className="rounded bg-slate-100 px-1 text-xs">Job_Requirements</code> with
        columns: <code className="rounded bg-slate-100 px-1 text-xs">role, department, location, required_skills, jd_text</code>.
      </p>
      <div className="space-y-1">
        <label className="block text-xs font-semibold text-slate-600">Excel / CSV File</label>
        <input type="file" accept=".xlsx,.xlsm,.csv"
          onChange={e => { setFile(e.target.files?.[0] ?? null); setResult(null); setError(""); }}
          className="block w-full text-sm text-slate-700 file:mr-3 file:rounded-lg file:border-0 file:bg-brand-50 file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-brand-700 hover:file:bg-brand-100" />
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {result && (
        <div className="rounded-xl border border-slate-100 bg-slate-50 px-4 py-3 space-y-2">
          <p className="text-sm font-semibold text-slate-700">Import complete</p>
          <div className="flex gap-4 text-sm">
            <span className="text-emerald-600 font-medium">+{result.created} created</span>
            <span className="text-brand-600 font-medium">{result.updated} updated</span>
            {result.failed > 0 && <span className="text-red-600 font-medium">{result.failed} failed</span>}
          </div>
          {result.errors.length > 0 && (
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {result.errors.map(e => (
                <p key={e.row} className="text-xs text-red-600">Row {e.row}: {e.error}</p>
              ))}
            </div>
          )}
          {result.created > 0 && (
            <button onClick={() => router.push("/job-posts")} className="button-primary text-xs mt-1">
              View Job Posts →
            </button>
          )}
        </div>
      )}

      <button onClick={handleUpload} disabled={!file || loading} className="button-primary">
        {loading ? <><Loader2 className="h-4 w-4 animate-spin" /> Importing…</> : <><Upload className="h-4 w-4" /> Import to Database</>}
      </button>
    </div>
  );
}

export default function JobRequirementsNewPage() {
  const [tab, setTab] = useState<Tab>("form");

  return (
    <div className="mx-auto max-w-2xl space-y-5">
      <div>
        <h1 className="page-title flex items-center gap-2"><Briefcase className="h-5 w-5 text-brand-600" /> New Job Requirement</h1>
        <p className="page-subtitle mt-0.5">Create a single job or bulk-import from Excel — both save directly to the database.</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 rounded-xl border border-slate-200 bg-slate-50 p-1 w-fit">
        <button onClick={() => setTab("form")}
          className={`flex items-center gap-1.5 rounded-lg px-4 py-2 text-xs font-semibold transition ${tab === "form" ? "bg-white text-brand-700 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}>
          <Plus className="h-3.5 w-3.5" /> Create Job
        </button>
        <button onClick={() => setTab("excel")}
          className={`flex items-center gap-1.5 rounded-lg px-4 py-2 text-xs font-semibold transition ${tab === "excel" ? "bg-white text-brand-700 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}>
          <FileText className="h-3.5 w-3.5" /> Bulk Import (Excel)
        </button>
      </div>

      {tab === "form"  && <JobForm />}
      {tab === "excel" && <ExcelUpload />}
    </div>
  );
}
