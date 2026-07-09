"use client";

import {
  Briefcase, ChevronDown, Database, FileText, LayoutDashboard,
  LogOut, PanelLeftClose, PanelLeftOpen, Shield, UserRound,
  Users, Bell, Search, Settings, Building2, Upload, Loader2, X
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, useRef, type ReactNode } from "react";
import { apiClient } from "../api/client";

type NavItem = { to: string; label: string; icon: React.ElementType; badge?: string };

const candidateNav: NavItem[] = [
  { to: "/jobs",         label: "Jobs",         icon: Briefcase },
  { to: "/applications", label: "Applications", icon: FileText },
  { to: "/profile",      label: "Profile",      icon: UserRound },
];

const operationsNav: NavItem[] = [
  { to: "/operations",           label: "Dashboard",        icon: LayoutDashboard },
  { to: "/job-requirements/new", label: "Job Requirements", icon: Briefcase },
  { to: "/job-posts",            label: "Job Posts",        icon: FileText },
  { to: "/batches",              label: "Batches",          icon: Database },
];

const adminNav: NavItem[] = [
  ...operationsNav,
  { to: "/candidates",    label: "Candidates",    icon: Users },
  { to: "/resume-intake", label: "Resume Intake", icon: Upload },
  { to: "/manage-users",  label: "Manage Users",  icon: Shield },
];

const ROLE_LABEL: Record<string, string> = {
  admin: "Administrator", hr: "HR Manager", recruiter: "Recruiter", candidate: "Candidate",
};

function NavLink({ item, collapsed, active }: { item: NavItem; collapsed: boolean; active: boolean }) {
  return (
    <Link href={item.to} title={item.label}
      className={`group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-150 ${
        active
          ? "bg-brand-600 text-white shadow-md shadow-brand-900/30"
          : "text-slate-400 hover:bg-white/[0.07] hover:text-slate-100"
      } ${collapsed ? "justify-center px-2.5" : ""}`}
    >
      <item.icon className={`h-[18px] w-[18px] flex-shrink-0 transition-colors ${active ? "text-white" : "text-slate-500 group-hover:text-slate-300"}`} />
      {!collapsed && <span className="truncate">{item.label}</span>}
      {!collapsed && item.badge && (
        <span className="ml-auto rounded-full bg-brand-500/30 px-2 py-0.5 text-2xs font-semibold text-brand-300">{item.badge}</span>
      )}
    </Link>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [role, setRole]           = useState("candidate");
  const [email, setEmail]         = useState("");

  useEffect(() => {
    setCollapsed(localStorage.getItem("hirex_sidebar_open") === "false");
    setRole(localStorage.getItem("hirex_role") || "candidate");
    setEmail(localStorage.getItem("hirex_email") || "");
  }, []);

  function toggleSidebar() {
    setCollapsed(c => {
      localStorage.setItem("hirex_sidebar_open", String(c));
      return !c;
    });
  }

  function logout() {
    localStorage.removeItem("hirex_token");
    localStorage.removeItem("hirex_role");
    localStorage.removeItem("hirex_email");
    window.location.href = "/login";
  }

  const nav      = role === "admin" ? adminNav : ["hr", "recruiter"].includes(role) ? operationsNav : candidateNav;
  const initials = email ? email.slice(0, 2).toUpperCase() : role.slice(0, 2).toUpperCase();
  const SIDEBAR_W = collapsed ? "w-[72px]" : "w-[264px]";

  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Sidebar */}
      <aside className={`fixed inset-y-0 left-0 z-30 hidden flex-col bg-[#0f172a] transition-[width] duration-200 ease-in-out md:flex ${SIDEBAR_W}`}
        style={{ borderRight: "1px solid rgba(255,255,255,0.05)" }}>

        {/* Logo */}
        <div className={`flex h-[64px] flex-shrink-0 items-center ${collapsed ? "justify-center px-2" : "gap-3 px-4"}`}
          style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
          <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-brand-600 shadow-lg shadow-brand-900/50">
            <Building2 className="h-[18px] w-[18px] text-white" />
          </div>
          {!collapsed && (
            <>
              <div className="min-w-0 flex-1">
                <p className="text-base font-extrabold leading-none tracking-tight text-white">HireX</p>
                <p className="mt-0.5 text-2xs font-semibold uppercase tracking-widest text-slate-500">Talent Ops</p>
              </div>
              <button onClick={toggleSidebar} title="Collapse"
                className="rounded-lg p-1.5 text-slate-600 transition hover:bg-white/[0.07] hover:text-slate-300">
                <PanelLeftClose className="h-[18px] w-[18px]" />
              </button>
            </>
          )}
        </div>

        {collapsed && (
          <button onClick={toggleSidebar} title="Expand"
            className="mx-auto mt-3 rounded-lg p-1.5 text-slate-600 transition hover:bg-white/[0.07] hover:text-slate-300">
            <PanelLeftOpen className="h-[18px] w-[18px]" />
          </button>
        )}

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto px-3 py-4">
          {!collapsed && (
            <p className="mb-2 px-2 text-2xs font-bold uppercase tracking-widest text-slate-600">
              {role === "candidate" ? "My Portal" : "Operations"}
            </p>
          )}
          <div className="space-y-0.5">
            {nav.map(item => (
              <NavLink key={item.to} item={item} collapsed={collapsed} active={pathname === item.to || pathname.startsWith(item.to + "/")} />
            ))}
          </div>

          {!collapsed && role === "admin" && (
            <>
              <div className="my-4" style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }} />
              <p className="mb-2 px-2 text-2xs font-bold uppercase tracking-widest text-slate-600">System</p>
              <Link href="/settings"
                className={`group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-150 ${
                  pathname === "/settings" ? "bg-brand-600 text-white shadow-md shadow-brand-900/30" : "text-slate-400 hover:bg-white/[0.07] hover:text-slate-100"
                }`}>
                <Settings className="h-[18px] w-[18px] flex-shrink-0 text-slate-500 group-hover:text-slate-300" />
                <span>Settings</span>
              </Link>
            </>
          )}
        </nav>

        {/* User footer */}
        <div className={`p-3 ${collapsed ? "flex justify-center" : ""}`}
          style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>
          {collapsed ? (
            <button onClick={logout} title="Sign out"
              className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/[0.06] text-slate-400 transition hover:bg-white/10 hover:text-slate-200">
              <LogOut className="h-[18px] w-[18px]" />
            </button>
          ) : (
            <div className="flex items-center gap-3 rounded-xl px-2 py-2.5">
              <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-brand-600/20 text-xs font-bold text-brand-400 ring-1 ring-brand-500/30">
                {initials}
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-slate-200">{email || ROLE_LABEL[role]}</p>
                <p className="text-2xs text-slate-500">{ROLE_LABEL[role]}</p>
              </div>
              <button onClick={logout} title="Sign out"
                className="rounded-lg p-1.5 text-slate-600 transition hover:bg-white/[0.07] hover:text-slate-300">
                <LogOut className="h-[18px] w-[18px]" />
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* Main content area */}
      <div className={`flex min-h-screen flex-1 flex-col transition-[margin] duration-200 ease-in-out ${collapsed ? "md:ml-[72px]" : "md:ml-[264px]"}`}>

        {/* Top bar */}
        <header className="sticky top-0 z-20 flex h-[64px] items-center gap-4 border-b border-slate-200 bg-white/90 px-6 backdrop-blur-md">
          <div className="flex-1">
            <div className="relative hidden max-w-sm sm:block z-50">
              <GlobalSearch />
            </div>
          </div>
          <div className="flex items-center gap-2.5">
            <button type="button" aria-label="Notifications" className="relative flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-white shadow-card-xs transition hover:bg-slate-50">
              <Bell className="h-[18px] w-[18px] text-slate-500" />
              <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-brand-600 ring-2 ring-white" />
            </button>
            <div className="h-7 w-px bg-slate-200" />
            <div className="flex items-center gap-2.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 shadow-card-xs">
              <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-brand-100 text-2xs font-bold text-brand-700">
                {initials}
              </div>
              <span className="hidden text-sm font-semibold text-slate-700 sm:block">{email || ROLE_LABEL[role]}</span>
              <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
            </div>
          </div>
        </header>

        <main className="flex-1 px-6 py-8 lg:px-8 lg:py-9">{children}</main>
      </div>

      {/* Mobile bottom nav */}
      <nav className="fixed inset-x-0 bottom-0 z-30 flex border-t border-slate-200 bg-white shadow-lg md:hidden">
        {nav.slice(0, 4).map(item => (
          <Link key={item.to} href={item.to}
            className={`flex min-h-[60px] flex-1 flex-col items-center justify-center gap-1 text-xs font-medium transition ${pathname === item.to ? "text-brand-600" : "text-slate-400"}`}>
            <item.icon className="h-5 w-5" />
            {item.label}
          </Link>
        ))}
      </nav>
    </div>
  );
}

function GlobalSearch() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<{ candidates: any[], jobs: any[] } | null>(null);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (!query || query.length < 2) {
      setResults(null);
      return;
    }
    setLoading(true);
    const timer = setTimeout(async () => {
      try {
        const res = await apiClient.get(`/admin/search?q=${encodeURIComponent(query)}`);
        setResults(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  function handleSelectJob(jobId: string) {
    setOpen(false);
    setQuery("");
    router.push(`/job-posts/${jobId}`);
  }

  function handleSelectCandidate(email: string) {
    setOpen(false);
    setQuery("");
    router.push(`/candidates?search=${encodeURIComponent(email)}`);
  }

  return (
    <div className="relative" ref={ref}>
      <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
      <input 
        type="search" 
        placeholder="Search candidates, jobs…"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          if (e.target.value.length >= 2) setOpen(true);
        }}
        onFocus={() => { if (query.length >= 2) setOpen(true); }}
        className="w-full rounded-xl border border-slate-200 bg-slate-50/80 py-2.5 pl-10 pr-4 text-sm text-slate-900 placeholder:text-slate-400 outline-none transition focus:border-brand-400 focus:bg-white focus:ring-[3px] focus:ring-brand-500/15" 
      />
      
      {open && (query.length >= 2) && (
        <div className="absolute top-full left-0 right-0 mt-2 rounded-xl border border-slate-200 bg-white shadow-xl max-h-[400px] overflow-y-auto z-50">
          {loading && !results && (
            <div className="flex justify-center p-4">
              <Loader2 className="h-5 w-5 animate-spin text-slate-400" />
            </div>
          )}
          
          {results && (
            <div className="py-2">
              {results.candidates.length > 0 && (
                <div className="mb-2">
                  <div className="px-3 py-1 text-xs font-semibold text-slate-400 uppercase tracking-wider">Candidates</div>
                  {results.candidates.map(c => (
                    <button key={c.id} onClick={() => handleSelectCandidate(c.email)}
                      className="w-full text-left px-4 py-2 hover:bg-slate-50 flex items-center gap-3 transition">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-50 text-brand-600">
                        <Users className="h-4 w-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-slate-900 truncate">{c.name}</div>
                        <div className="text-xs text-slate-500 truncate">{c.role}</div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
              
              {results.jobs.length > 0 && (
                <div>
                  <div className="px-3 py-1 text-xs font-semibold text-slate-400 uppercase tracking-wider">Jobs</div>
                  {results.jobs.map(j => (
                    <button key={j.id} onClick={() => handleSelectJob(j.id)}
                      className="w-full text-left px-4 py-2 hover:bg-slate-50 flex items-center gap-3 transition">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-amber-50 text-amber-600">
                        <Briefcase className="h-4 w-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-slate-900 truncate">{j.title}</div>
                        <div className="text-xs text-slate-500 truncate">{j.department}</div>
                      </div>
                    </button>
                  ))}
                </div>
              )}

              {results.candidates.length === 0 && results.jobs.length === 0 && !loading && (
                <div className="px-4 py-6 text-center text-sm text-slate-500">
                  No results found for "{query}"
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
