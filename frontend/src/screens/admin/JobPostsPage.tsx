"use client";

import {
  FileText, Plus, Search, Loader2, RefreshCw, Trash2, Eye,
  ChevronLeft, ChevronRight, ChevronDown
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "../../api/client";

type JobPost = {
  job_id: string;
  title: string;
  department: string;
  location: string;
  employment_type: string;
  experience_min: number | null;
  experience_max: number | null;
  status: string;
  total_applications: number;
};

const STATUSES = ["open", "draft", "closed", "paused"];
const STATUS_BADGE: Record<string, string> = {
  open:   "badge-green",
  draft:  "badge-purple",
  closed: "badge-slate",
  paused: "badge-yellow",
};

const PAGE_SIZE = 20;

function StatusCell({ post, onChange }: { post: JobPost; onChange: (id: string, s: string) => void }) {
  const [open, setOpen]     = useState(false);
  const [saving, setSaving] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function close(e: MouseEvent) { if (!ref.current?.contains(e.target as Node)) setOpen(false); }
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  async function pick(s: string) {
    setOpen(false);
    if (s === post.status) return;
    setSaving(true);
    try {
      await apiClient.patch(`/jobs/${post.job_id}/status`, { status: s });
      onChange(post.job_id, s);
    } catch { /* keep old */ }
    finally { setSaving(false); }
  }

  return (
    <div ref={ref} className="relative inline-block">
      <button onClick={e => { e.stopPropagation(); setOpen(o => !o); }}
        disabled={saving}
        className={`${STATUS_BADGE[post.status] ?? "badge-slate"} inline-flex items-center gap-1 cursor-pointer`}>
        {saving ? <Loader2 className="h-3 w-3 animate-spin" /> : post.status}
        <ChevronDown className="h-3 w-3" />
      </button>
      {open && (
        <div className="absolute left-0 top-full z-20 mt-1 min-w-[110px] rounded-xl border border-slate-200 bg-white shadow-card-lg py-1">
          {STATUSES.map(s => (
            <button key={s} onClick={() => pick(s)}
              className={`flex w-full items-center gap-2 px-3 py-1.5 text-xs font-medium hover:bg-slate-50 ${s === post.status ? "text-brand-600" : "text-slate-700"}`}>
              <span className={`h-1.5 w-1.5 rounded-full ${
                s === "open" ? "bg-emerald-500" : s === "draft" ? "bg-purple-500" : s === "paused" ? "bg-amber-500" : "bg-slate-400"
              }`} />
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export function JobPostsPage() {
  const router = useRouter();
  const [posts, setPosts]   = useState<JobPost[]>([]);
  const [total, setTotal]   = useState(0);
  const [page, setPage]     = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading]   = useState(true);
  const [toast, setToast]       = useState("");

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  function showToast(m: string) { setToast(m); setTimeout(() => setToast(""), 3000); }

  const load = useCallback(async (q: string, s: string) => {
    setLoading(true);
    try {
      const res = await apiClient.get("/jobs/list", {
        params: { search: q || undefined, status: s || undefined },
      });
      const data = res.data;
      const items = data.jobs ?? data ?? [];
      setPosts(items);
      setTotal(data.total ?? items.length);
    } catch {
      setPosts([]); setTotal(0);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(search, statusFilter); }, [load, search, statusFilter]);

  function handleSearch(q: string) { setSearch(q); setPage(1); }
  function handleStatusFilter(s: string) { setStatusFilter(s === statusFilter ? "" : s); setPage(1); }

  function updateStatus(id: string, status: string) {
    setPosts(p => p.map(j => j.job_id === id ? { ...j, status } : j));
  }

  function toggleSelect(id: string) {
    setSelected(prev => { const next = new Set(prev); next.has(id) ? next.delete(id) : next.add(id); return next; });
  }

  function toggleAll() {
    const pageItems = paged.map(j => j.job_id);
    if (pageItems.every(id => selected.has(id))) {
      setSelected(prev => { const n = new Set(prev); pageItems.forEach(id => n.delete(id)); return n; });
    } else {
      setSelected(prev => { const n = new Set(prev); pageItems.forEach(id => n.add(id)); return n; });
    }
  }

  async function deleteSelected() {
    showToast("Bulk delete is not available in this version.");
    setSelected(new Set());
  }

  // Client-side pagination since /jobs/list returns all results
  const paged = posts.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const statCounts: Record<string, number> = { open: 0, draft: 0, closed: 0, paused: 0 };
  posts.forEach(p => { if (p.status in statCounts) statCounts[p.status]++; });

  return (
    <div className="mx-auto max-w-[1200px] space-y-5">
      {toast && <div className="fixed bottom-6 right-6 z-50 rounded-xl border bg-white px-4 py-3 text-sm shadow-card-lg animate-fade-in">{toast}</div>}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title flex items-center gap-2"><FileText className="h-5 w-5 text-brand-600" /> Job Posts</h1>
          <p className="page-subtitle mt-0.5">{total} total · Page {page} of {totalPages}</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => load(search, statusFilter)} disabled={loading} className="button-secondary">
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          <a href="/job-requirements/new" className="button-primary"><Plus className="h-4 w-4" /> New Job</a>
        </div>
      </div>

      {/* Status filters */}
      <div className="flex flex-wrap gap-2">
        {(["open", "draft", "paused", "closed"] as const).map(s => (
          <button key={s} onClick={() => handleStatusFilter(s)}
            className={`rounded-full px-3.5 py-1.5 text-xs font-semibold transition border ${statusFilter === s ? "border-brand-500 bg-brand-600 text-white" : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"}`}>
            {s.charAt(0).toUpperCase() + s.slice(1)} <span className="opacity-60">({statCounts[s]})</span>
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="relative max-w-xs">
        <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input className="input pl-10" placeholder="Search title, department…"
          value={search} onChange={e => handleSearch(e.target.value)} />
      </div>

      {/* Bulk bar */}
      {selected.size > 0 && (
        <div className="flex items-center gap-3 rounded-xl border border-brand-200 bg-brand-50 px-4 py-2.5 animate-fade-in">
          <span className="text-sm font-medium text-brand-700">{selected.size} selected</span>
          <button onClick={deleteSelected} className="button-danger py-1.5 text-xs"><Trash2 className="h-3.5 w-3.5" /> Delete</button>
          <button onClick={() => setSelected(new Set())} className="button-secondary py-1.5 text-xs">Clear</button>
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
                  <th className="w-8">
                    <input type="checkbox" className="rounded border-slate-300"
                      checked={paged.length > 0 && paged.every(j => selected.has(j.job_id))}
                      onChange={toggleAll} />
                  </th>
                  <th>Title</th>
                  <th>Department</th>
                  <th>Location</th>
                  <th>Type</th>
                  <th>Experience</th>
                  <th>Applications</th>
                  <th>Status</th>
                  <th className="text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {paged.length === 0 && (
                  <tr>
                    <td colSpan={9} className="py-20 text-center text-slate-400">
                      <FileText className="mx-auto mb-2 h-8 w-8 text-slate-200" />
                      {search ? `No results for "${search}"` : "No job posts yet. Create one to get started."}
                    </td>
                  </tr>
                )}
                {paged.map(j => (
                  <tr key={j.job_id} className="cursor-pointer hover:bg-slate-50/60" onClick={() => router.push(`/job-posts/${j.job_id}`)}>
                    <td onClick={e => e.stopPropagation()}>
                      <input type="checkbox" className="rounded border-slate-300"
                        checked={selected.has(j.job_id)}
                        onChange={() => toggleSelect(j.job_id)} />
                    </td>
                    <td className="font-semibold text-slate-800">{j.title}</td>
                    <td className="text-slate-600">{j.department}</td>
                    <td className="text-slate-500">{j.location}</td>
                    <td><span className="badge-slate">{j.employment_type}</span></td>
                    <td className="text-xs text-slate-500">
                      {j.experience_min != null && j.experience_max != null
                        ? `${j.experience_min}–${j.experience_max} yrs`
                        : j.experience_min != null
                          ? `${j.experience_min}+ yrs`
                          : "—"}
                    </td>
                    <td className="font-medium text-slate-700">{j.total_applications}</td>
                    <td onClick={e => e.stopPropagation()}>
                      <StatusCell post={j} onChange={updateStatus} />
                    </td>
                    <td className="text-right" onClick={e => e.stopPropagation()}>
                      <button
                        onClick={() => router.push(`/job-posts/${j.job_id}`)}
                        className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-600 hover:border-brand-300 hover:bg-brand-50 hover:text-brand-700 transition">
                        <Eye className="h-3.5 w-3.5" /> View
                      </button>
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
          {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => i + 1).map(p => (
            <button key={p} onClick={() => setPage(p)}
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
