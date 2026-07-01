"use client";

import { useEffect, useState } from "react";
import {
  FileText, Loader2, RefreshCw, CheckCircle2, Clock,
  XCircle, AlertCircle, Briefcase, Trash2
} from "lucide-react";
import { apiClient } from "../../api/client";

type Application = {
  application_id: string;
  requirement_id: string;
  role?: string;
  department?: string;
  status: string;
  created_at: string;
  updated_at?: string;
};

const STATUS_CONFIG: Record<string, { badge: string; icon: React.ElementType; label: string }> = {
  submitted:    { badge: "badge-blue",   icon: Clock,         label: "Submitted"    },
  under_review: { badge: "badge-yellow", icon: AlertCircle,   label: "Under Review" },
  shortlisted:  { badge: "badge-green",  icon: CheckCircle2,  label: "Shortlisted"  },
  rejected:     { badge: "badge-red",    icon: XCircle,       label: "Not Selected" },
  hired:        { badge: "badge-purple", icon: CheckCircle2,  label: "Hired!"       },
  withdrawn:    { badge: "badge-slate",  icon: Trash2,        label: "Withdrawn"    },
};

const PIPELINE = ["submitted", "under_review", "shortlisted", "hired"];

function StatusPipeline({ status }: { status: string }) {
  const idx = PIPELINE.indexOf(status);
  if (status === "rejected" || status === "withdrawn") {
    return <span className={STATUS_CONFIG[status]?.badge ?? "badge-slate"}>{STATUS_CONFIG[status]?.label ?? status}</span>;
  }
  return (
    <div className="flex items-center gap-1">
      {PIPELINE.map((s, i) => {
        const done    = i <= idx;
        const current = i === idx;
        return (
          <div key={s} className="flex items-center gap-1">
            <div className={`h-2 w-2 rounded-full transition ${done ? (current ? "bg-brand-600 ring-2 ring-brand-200" : "bg-emerald-500") : "bg-slate-200"}`} />
            {i < PIPELINE.length - 1 && <div className={`h-px w-4 ${i < idx ? "bg-emerald-400" : "bg-slate-200"}`} />}
          </div>
        );
      })}
      <span className={`ml-1.5 ${STATUS_CONFIG[status]?.badge ?? "badge-slate"}`}>{STATUS_CONFIG[status]?.label ?? status}</span>
    </div>
  );
}

export default function ApplicationsPage() {
  const [apps, setApps]           = useState<Application[]>([]);
  const [loading, setLoading]     = useState(true);
  const [withdrawing, setWith]    = useState<string | null>(null);
  const [toast, setToast]         = useState("");

  function showToast(msg: string) { setToast(msg); setTimeout(() => setToast(""), 2500); }

  function load() {
    setLoading(true);
    apiClient.get<{ applications: Application[] }>("/applications/list")
      .then(r => setApps(r.data.applications ?? []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  async function withdraw(appId: string) {
    if (!confirm("Withdraw this application?")) return;
    setWith(appId);
    try {
      await apiClient.patch(`/applications/${appId}/withdraw`);
      setApps(prev => prev.map(a => a.application_id === appId ? { ...a, status: "withdrawn" } : a));
      showToast("Application withdrawn.");
    } catch {
      showToast("Withdraw failed. Please try again.");
    } finally {
      setWith(null);
    }
  }

  const counts = {
    total:       apps.length,
    active:      apps.filter(a => !["rejected","withdrawn"].includes(a.status)).length,
    shortlisted: apps.filter(a => a.status === "shortlisted").length,
    hired:       apps.filter(a => a.status === "hired").length,
  };

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 rounded-xl border bg-white px-4 py-3 text-sm font-medium shadow-card-lg animate-fade-in">{toast}</div>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title flex items-center gap-2"><FileText className="h-5 w-5 text-brand-600" /> My Applications</h1>
          <p className="page-subtitle mt-0.5">Track the status of your job applications.</p>
        </div>
        <button onClick={load} disabled={loading} className="button-secondary">
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Stats */}
      {!loading && apps.length > 0 && (
        <div className="grid grid-cols-4 gap-3">
          {[
            ["Total",       counts.total,       "text-slate-700"],
            ["Active",      counts.active,       "text-brand-600"],
            ["Shortlisted", counts.shortlisted,  "text-emerald-600"],
            ["Hired",       counts.hired,        "text-purple-600"],
          ].map(([label, value, color]) => (
            <div key={label as string} className="stat-card text-center">
              <span className="stat-label">{label}</span>
              <span className={`stat-value ${color}`}>{value}</span>
            </div>
          ))}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-16"><Loader2 className="h-6 w-6 animate-spin text-slate-400" /></div>
      ) : apps.length === 0 ? (
        <div className="card card-body py-16 text-center text-slate-400">
          <FileText className="mx-auto mb-3 h-10 w-10 text-slate-200" />
          <p className="font-medium text-slate-600">No applications yet</p>
          <p className="mt-1 text-sm">Browse open positions and apply to get started.</p>
          <a href="/jobs" className="button-primary mt-4 inline-flex">
            <Briefcase className="h-4 w-4" /> Browse Jobs
          </a>
        </div>
      ) : (
        <div className="space-y-3">
          {apps.map(a => {
            const cfg   = STATUS_CONFIG[a.status];
            const Icon  = cfg?.icon ?? FileText;
            const canWd = !["rejected","withdrawn","hired"].includes(a.status);
            return (
              <div key={a.application_id} className="card card-body">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <div className={`mt-0.5 flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl ${a.status === "hired" ? "bg-purple-50" : a.status === "shortlisted" ? "bg-emerald-50" : a.status === "rejected" ? "bg-red-50" : "bg-brand-50"}`}>
                      <Icon className={`h-4 w-4 ${a.status === "hired" ? "text-purple-600" : a.status === "shortlisted" ? "text-emerald-600" : a.status === "rejected" ? "text-red-500" : "text-brand-600"}`} />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-slate-800">{a.role ?? a.requirement_id}</p>
                      {a.department && <p className="text-xs text-slate-500">{a.department}</p>}
                      <p className="mt-0.5 text-2xs text-slate-400">Applied {new Date(a.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}</p>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <StatusPipeline status={a.status} />
                    {canWd && (
                      <button onClick={() => withdraw(a.application_id)} disabled={withdrawing === a.application_id}
                        className="text-2xs text-slate-400 hover:text-red-500 transition flex items-center gap-1">
                        {withdrawing === a.application_id ? <Loader2 className="h-3 w-3 animate-spin" /> : <Trash2 className="h-3 w-3" />}
                        Withdraw
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
