"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Users, Briefcase, CheckCircle2, Clock, TrendingUp, Loader2,
  Upload, Database, Shield, FileText, ArrowRight, RefreshCw,
  UserCheck, UserX, Zap
} from "lucide-react";
import { apiClient } from "../../api/client";

type Summary = {
  total_candidates: number;
  total_applications: number;
  active_requirements: number;
  pending_reviews: number;
  fresh_candidates?: number;
  stale_candidates?: number;
  available_pool?: number;
  resumes_this_week?: number;
};

const quickLinks = [
  { href: "/resume-intake",       icon: Upload,       label: "Upload Resumes",     desc: "Parse & add candidates",    color: "text-brand-600",   bg: "bg-brand-50"   },
  { href: "/candidates",          icon: Users,        label: "Candidate Master",   desc: "View & filter all talent",  color: "text-sky-600",     bg: "bg-sky-50"     },
  { href: "/job-posts",           icon: FileText,     label: "Job Posts",          desc: "Manage active openings",    color: "text-emerald-600", bg: "bg-emerald-50" },
  { href: "/job-requirements/new",icon: Briefcase,    label: "Upload Requirements",desc: "Add new job requirements",  color: "text-amber-600",   bg: "bg-amber-50"   },
  { href: "/batches",             icon: Database,     label: "Sourcing Batches",   desc: "Review import history",     color: "text-purple-600",  bg: "bg-purple-50"  },
  { href: "/vapi-configuration",  icon: Zap,          label: "Vapi Configuration", desc: "Manage AI interviewer",     color: "text-indigo-600",  bg: "bg-indigo-50"  },
  { href: "/manage-users",        icon: Shield,       label: "Manage Users",       desc: "Create & control access",   color: "text-rose-600",    bg: "bg-rose-50"    },
];

export default function OperationsDashboardPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  function load() {
    setLoading(true);
    apiClient.get<Summary>("/admin/summary")
      .then(r => { setSummary(r.data); setLastRefresh(new Date()); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  const stats = [
    { label: "Total Candidates",  value: summary?.total_candidates ?? 0,    icon: Users,        color: "text-brand-600",   bg: "bg-brand-50",   href: "/candidates" },
    { label: "Applications",      value: summary?.total_applications ?? 0,  icon: Briefcase,    color: "text-emerald-600", bg: "bg-emerald-50", href: "/all-applications"  },
    { label: "Active Roles",      value: summary?.active_requirements ?? 0, icon: CheckCircle2, color: "text-sky-600",     bg: "bg-sky-50",     href: "/job-posts"  },
    { label: "Pending Review",    value: summary?.pending_reviews ?? 0,     icon: Clock,        color: "text-amber-600",   bg: "bg-amber-50",   href: "/all-applications?decision=REVIEW" },
  ];

  const pipelineStats = [
    { label: "Fresh Profiles",    value: summary?.fresh_candidates ?? "—",  icon: UserCheck, color: "text-emerald-600" },
    { label: "Stale Profiles",    value: summary?.stale_candidates ?? "—",  icon: UserX,     color: "text-amber-600"   },
    { label: "Available Pool",    value: summary?.available_pool ?? "—",    icon: Zap,       color: "text-brand-600"   },
    { label: "Resumes This Week", value: summary?.resumes_this_week ?? "—", icon: Upload,    color: "text-purple-600"  },
  ];

  return (
    <div className="mx-auto max-w-[1200px] space-y-7">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title flex items-center gap-2"><TrendingUp className="h-5 w-5 text-brand-600" /> Operations Dashboard</h1>
          <p className="page-subtitle mt-0.5">
            Hiring pipeline overview · Last refreshed {lastRefresh.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
          </p>
        </div>
        <button onClick={load} disabled={loading} className="button-secondary">
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} /> Refresh
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-16"><Loader2 className="h-6 w-6 animate-spin text-slate-400" /></div>
      ) : (
        <>
          {/* Primary stats */}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {stats.map(({ label, value, icon: Icon, color, bg, href }) => (
              <Link key={label} href={href} className="stat-card hover:shadow-card-md transition-shadow">
                <div className={`mb-2 flex h-10 w-10 items-center justify-center rounded-xl ${bg}`}>
                  <Icon className={`h-5 w-5 ${color}`} />
                </div>
                <span className="stat-label">{label}</span>
                <span className="stat-value">{typeof value === "number" ? value.toLocaleString() : value}</span>
              </Link>
            ))}
          </div>

          {/* Pipeline health */}
          <div className="card overflow-hidden">
            <div className="card-header">
              <h2 className="section-label">Pipeline Health</h2>
            </div>
            <div className="grid grid-cols-2 divide-x divide-y divide-slate-100 sm:grid-cols-4">
              {pipelineStats.map(({ label, value, icon: Icon, color }) => (
                <div key={label} className="flex flex-col gap-1 px-5 py-4">
                  <div className="flex items-center gap-2">
                    <Icon className={`h-4 w-4 ${color}`} />
                    <span className="stat-label">{label}</span>
                  </div>
                  <span className="text-xl font-bold text-slate-800">{typeof value === "number" ? value.toLocaleString() : value}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {/* Quick links */}
      <div>
        <h2 className="section-label mb-3">Quick Actions</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {quickLinks.map(({ href, icon: Icon, label, desc, color, bg }) => (
            <Link key={href} href={href}
              className="group flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-card-sm transition hover:shadow-card-md hover:border-brand-200">
              <div className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl ${bg}`}>
                <Icon className={`h-5 w-5 ${color}`} />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-slate-800">{label}</p>
                <p className="text-xs text-slate-400 truncate">{desc}</p>
              </div>
              <ArrowRight className="h-4 w-4 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-brand-500" />
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
