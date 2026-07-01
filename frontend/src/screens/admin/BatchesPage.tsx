"use client";

import { useEffect, useState } from "react";
import { Database, Loader2, RefreshCw } from "lucide-react";
import { apiClient } from "../../api/client";

type Batch = { sourcing_batch_id: string; source_type: string; source_label: string; status: string; total_candidates: number; new_candidates: number; created_at: string };

const STATUS_BADGE: Record<string, string> = { IMPORTED: "badge-blue", PROCESSING: "badge-yellow", COMPLETED: "badge-green", FAILED: "badge-red" };

export default function BatchesPage() {
  const [batches, setBatches] = useState<Batch[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    apiClient.get<Batch[] | { items: Batch[] }>("/admin/sourcing-batches").then(r => { const d = r.data; setBatches(Array.isArray(d) ? d : (d as { items: Batch[] }).items ?? []); }).catch(() => setBatches([])).finally(() => setLoading(false));
  };
  useEffect(() => { load(); }, []);

  return (
    <div className="mx-auto max-w-[1100px] space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title flex items-center gap-2"><Database className="h-5 w-5 text-brand-600" /> Sourcing Batches</h1>
          <p className="page-subtitle mt-0.5">All candidate import batches and their status.</p>
        </div>
        <button onClick={load} disabled={loading} className="button-secondary"><RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} /></button>
      </div>

      <div className="card overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-16"><Loader2 className="h-6 w-6 animate-spin text-slate-400" /></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead><tr>
                <th>Batch ID</th><th>Source</th><th>Label</th><th>Status</th><th>Total</th><th>New</th><th>Date</th>
              </tr></thead>
              <tbody>
                {batches.length === 0 && (
                  <tr><td colSpan={7} className="py-16 text-center text-slate-400"><Database className="mx-auto mb-2 h-8 w-8 text-slate-200" /> No batches yet</td></tr>
                )}
                {batches.map(b => (
                  <tr key={b.sourcing_batch_id}>
                    <td className="font-mono text-xs text-slate-500">{b.sourcing_batch_id.slice(0,8)}…</td>
                    <td><span className="badge-slate capitalize">{b.source_type}</span></td>
                    <td className="text-slate-700">{b.source_label}</td>
                    <td><span className={STATUS_BADGE[b.status] ?? "badge-slate"}>{b.status}</span></td>
                    <td>{b.total_candidates}</td>
                    <td className="text-emerald-600 font-semibold">+{b.new_candidates}</td>
                    <td className="text-xs text-slate-400">{new Date(b.created_at).toLocaleDateString("en-GB")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
