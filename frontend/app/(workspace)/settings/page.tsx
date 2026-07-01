"use client";

import { Settings, Shield, Bell, Database, Server, RefreshCw, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { apiClient } from "../../../src/api/client";

type HealthStatus = { status: string } | null;

export default function SettingsPage() {
  const [health, setHealth]   = useState<HealthStatus>(null);
  const [loading, setLoading] = useState(true);

  function checkHealth() {
    setLoading(true);
    apiClient.get("/health")
      .then(r => setHealth(r.data))
      .catch(() => setHealth({ status: "unreachable" }))
      .finally(() => setLoading(false));
  }

  useEffect(() => { checkHealth(); }, []);

  const sections = [
    {
      icon: Shield,
      title: "Security",
      color: "text-brand-600",
      bg: "bg-brand-50",
      items: [
        { label: "JWT Authentication", value: "Enabled", status: "ok" },
        { label: "CORS Policy", value: "Localhost only (dev)", status: "warn" },
        { label: "Password Policy", value: "Min 8 characters", status: "ok" },
      ],
    },
    {
      icon: Bell,
      title: "Notifications",
      color: "text-amber-600",
      bg: "bg-amber-50",
      items: [
        { label: "Email Alerts", value: "Not configured", status: "warn" },
        { label: "Slack Integration", value: "Not configured", status: "warn" },
      ],
    },
    {
      icon: Database,
      title: "Data",
      color: "text-sky-600",
      bg: "bg-sky-50",
      items: [
        { label: "Database", value: "PostgreSQL (via SQLAlchemy)", status: "ok" },
        { label: "File Storage", value: "Local filesystem", status: "ok" },
        { label: "Resume Parser", value: "AI-assisted (enabled)", status: "ok" },
      ],
    },
  ];

  return (
    <div className="mx-auto max-w-[900px] space-y-7">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title flex items-center gap-2"><Settings className="h-5 w-5 text-brand-600" /> System Settings</h1>
          <p className="page-subtitle mt-0.5">Platform configuration and health overview.</p>
        </div>
      </div>

      {/* Backend health */}
      <div className="card card-body">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50">
              <Server className="h-5 w-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-800">Backend API</p>
              <p className="text-xs text-slate-400">FastAPI · http://127.0.0.1:8002</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
            ) : (
              <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${health?.status === "ok" ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}>
                <span className={`h-1.5 w-1.5 rounded-full ${health?.status === "ok" ? "bg-emerald-500" : "bg-red-500"}`} />
                {health?.status === "ok" ? "Healthy" : "Unreachable"}
              </span>
            )}
            <button onClick={checkHealth} disabled={loading} className="button-secondary py-1.5 text-xs">
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} /> Check
            </button>
          </div>
        </div>
      </div>

      {/* Config sections */}
      <div className="grid gap-5 sm:grid-cols-1">
        {sections.map(({ icon: Icon, title, color, bg, items }) => (
          <div key={title} className="card overflow-hidden">
            <div className="card-header flex items-center gap-2">
              <div className={`flex h-7 w-7 items-center justify-center rounded-lg ${bg}`}>
                <Icon className={`h-4 w-4 ${color}`} />
              </div>
              <span className="text-sm font-semibold text-slate-700">{title}</span>
            </div>
            <div className="divide-y divide-slate-50">
              {items.map(({ label, value, status }) => (
                <div key={label} className="flex items-center justify-between px-5 py-3">
                  <span className="text-sm text-slate-600">{label}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-slate-700">{value}</span>
                    <span className={`h-2 w-2 rounded-full ${status === "ok" ? "bg-emerald-400" : "bg-amber-400"}`} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <p className="text-center text-xs text-slate-400">HireX v0.1.0 · Talent Operations Platform</p>
    </div>
  );
}
