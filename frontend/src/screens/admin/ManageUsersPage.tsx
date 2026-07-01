"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Shield, Search, Loader2, RefreshCw, Key, Trash2, Plus, X, Eye, EyeOff, ToggleLeft, ToggleRight, Pencil, Check } from "lucide-react";
import { apiClient } from "../../api/client";

type User = { id: string; email: string; role: string; is_active: boolean; created_at: string };

function RoleCell({ user, onChange }: { user: User; onChange: (id: string, role: string) => void }) {
  const ROLES = ["admin", "hr", "recruiter", "candidate"];
  const ROLE_BADGE: Record<string, string> = { admin: "badge-red", hr: "badge-blue", recruiter: "badge-purple", candidate: "badge-slate" };
  const [editing, setEditing] = useState(false);
  const [saving, setSaving]   = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function close(e: MouseEvent) { if (!ref.current?.contains(e.target as Node)) setEditing(false); }
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  async function pick(role: string) {
    if (role === user.role) { setEditing(false); return; }
    setSaving(true);
    try {
      await apiClient.patch(`/admin/users/${user.id}`, { role });
      onChange(user.id, role);
    } catch { /* keep old */ }
    finally { setSaving(false); setEditing(false); }
  }

  return (
    <div ref={ref} className="relative inline-block">
      <button onClick={() => setEditing(v => !v)} disabled={saving}
        className={`${ROLE_BADGE[user.role] ?? "badge-slate"} inline-flex items-center gap-1 cursor-pointer`}>
        {saving ? <Loader2 className="h-3 w-3 animate-spin" /> : user.role}
        <Pencil className="h-2.5 w-2.5 opacity-60" />
      </button>
      {editing && (
        <div className="absolute left-0 top-full z-20 mt-1 min-w-[120px] rounded-xl border border-slate-200 bg-white shadow-card-lg py-1">
          {ROLES.map(r => (
            <button key={r} onClick={() => pick(r)}
              className={`flex w-full items-center gap-2 px-3 py-1.5 text-xs font-medium hover:bg-slate-50 ${r === user.role ? "text-brand-600" : "text-slate-700"}`}>
              {r === user.role && <Check className="h-3 w-3" />}
              <span className={`capitalize ${r === user.role ? "ml-0" : "ml-3.5"}`}>{r}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

const ROLES = ["admin", "hr", "recruiter", "candidate"];

function ResetPasswordModal({ user, onClose }: { user: User; onClose: () => void }) {
  const [pass, setPass]       = useState("");
  const [confirm, setConfirm] = useState("");
  const [show, setShow]       = useState(false);
  const [saving, setSaving]   = useState(false);
  const [error, setError]     = useState("");
  const [done, setDone]       = useState(false);

  const strength = pass.length === 0 ? 0 : pass.length < 6 ? 1 : pass.length < 10 ? 2 : 3;
  const strengthColor = ["bg-slate-200", "bg-red-500", "bg-amber-400", "bg-emerald-500"][strength];

  async function save() {
    if (pass !== confirm) { setError("Passwords do not match."); return; }
    if (pass.length < 8)  { setError("Minimum 8 characters."); return; }
    setSaving(true); setError("");
    try {
      await apiClient.post(`/admin/users/${user.id}/reset-password`, { password: pass });
      setDone(true);
      setTimeout(onClose, 1200);
    } catch { setError("Reset failed."); }
    finally { setSaving(false); }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
          <h3 className="text-sm font-semibold text-slate-800">Reset Password — {user.email}</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><X className="h-4 w-4" /></button>
        </div>
        <div className="space-y-4 px-6 py-5">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-600">New Password</label>
            <div className="relative">
              <input type={show ? "text" : "password"} value={pass} onChange={e => setPass(e.target.value)} className="input pr-10" placeholder="Min 6 characters" />
              <button type="button" onClick={() => setShow(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">
                {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            <div className="flex gap-1 mt-1">
              {[1,2,3].map(i => <div key={i} className={`h-1 flex-1 rounded-full ${i <= strength ? strengthColor : "bg-slate-200"}`} />)}
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-600">Confirm Password</label>
            <input type="password" value={confirm} onChange={e => setConfirm(e.target.value)} className="input" placeholder="Re-enter password" />
          </div>
          {error && <p className="text-xs text-red-600">{error}</p>}
          {done  && <p className="text-xs text-emerald-600">Password reset successfully!</p>}
          <button onClick={save} disabled={saving || done} className="button-primary w-full">
            {saving ? <><Loader2 className="h-4 w-4 animate-spin" /> Saving…</> : "Reset Password"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function ManageUsersPage() {
  const [users, setUsers]       = useState<User[]>([]);
  const [loading, setLoading]   = useState(true);
  const [search, setSearch]     = useState("");
  const [roleFilter, setRole]   = useState("all");
  const [toast, setToast]       = useState("");
  const [resetUser, setResetUser] = useState<User | null>(null);
  const [newEmail, setNewEmail]   = useState("");
  const [newRole, setNewRole]     = useState("recruiter");
  const [creating, setCreating]   = useState(false);
  const [showCreate, setShowCreate] = useState(false);

  function showToast(msg: string) { setToast(msg); setTimeout(() => setToast(""), 3000); }

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiClient.get<{ users: User[] }>("/admin/users");
      setUsers(res.data.users ?? []);
    } catch { showToast("Failed to load users"); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = users.filter(u => {
    const q = search.toLowerCase();
    return (roleFilter === "all" || u.role === roleFilter) &&
      (!q || u.email.toLowerCase().includes(q) || u.role.includes(q));
  });

  async function deleteUser(id: string) {
    if (!confirm("Delete this user?")) return;
    try { await apiClient.delete(`/admin/users/${id}`); setUsers(p => p.filter(u => u.id !== id)); showToast("User deleted"); }
    catch { showToast("Delete failed"); }
  }

  async function toggleActive(u: User) {
    try {
      await apiClient.patch(`/admin/users/${u.id}`, { is_active: !u.is_active });
      setUsers(p => p.map(x => x.id === u.id ? { ...x, is_active: !x.is_active } : x));
      showToast(u.is_active ? "User deactivated" : "User activated");
    } catch { showToast("Update failed"); }
  }

  function updateRole(id: string, role: string) {
    setUsers(p => p.map(u => u.id === id ? { ...u, role } : u));
    showToast("Role updated");
  }

  async function createUser() {
    if (!newEmail) return;
    setCreating(true);
    try {
      await apiClient.post("/admin/users", { email: newEmail, role: newRole, password: Math.random().toString(36).slice(-10) });
      showToast("User created"); setNewEmail(""); setShowCreate(false); load();
    } catch { showToast("Create failed"); }
    finally { setCreating(false); }
  }

  const counts = {
    total: users.length,
    admin: users.filter(u => u.role==="admin").length,
    hr: users.filter(u => u.role==="hr").length,
    recruiter: users.filter(u => u.role==="recruiter").length,
    candidate: users.filter(u => u.role==="candidate").length,
  };

  return (
    <div className="mx-auto max-w-[1100px] space-y-5">
      {toast && <div className="fixed bottom-6 right-6 z-50 rounded-xl border bg-white px-4 py-3 text-sm font-medium shadow-card-lg animate-fade-in">{toast}</div>}
      {resetUser && <ResetPasswordModal user={resetUser} onClose={() => setResetUser(null)} />}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title flex items-center gap-2"><Shield className="h-5 w-5 text-brand-600" /> Manage Users</h1>
          <p className="page-subtitle mt-0.5">Create, edit and manage all HireX user accounts.</p>
        </div>
        <div className="flex gap-2">
          <button onClick={load} disabled={loading} className="button-secondary"><RefreshCw className={`h-4 w-4 ${loading?"animate-spin":""}`} /></button>
          <button onClick={() => setShowCreate(v => !v)} className="button-primary"><Plus className="h-4 w-4" /> New User</button>
        </div>
      </div>

      {showCreate && (
        <div className="card card-body flex flex-wrap items-end gap-3">
          <div className="flex-1 space-y-1">
            <label className="text-xs font-semibold text-slate-600">Email</label>
            <input className="input" placeholder="user@company.com" value={newEmail} onChange={e => setNewEmail(e.target.value)} />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-600">Role</label>
            <select className="input w-36" value={newRole} onChange={e => setNewRole(e.target.value)}>
              {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <button onClick={createUser} disabled={creating} className="button-primary">
            {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />} Create
          </button>
        </div>
      )}

      <div className="grid grid-cols-5 gap-3">
        {([ ["Total", users.length, "all"], ["Admin", counts.admin, "admin"], ["HR", counts.hr, "hr"], ["Recruiter", counts.recruiter, "recruiter"], ["Candidate", counts.candidate, "candidate"] ] as [string, number, string][]).map(([label, n, key]) => (
          <button key={label} onClick={() => setRole(key)} className={`stat-card text-left ${roleFilter===key?"ring-2 ring-brand-500":""}`}>
            <span className="stat-label">{label}</span>
            <span className="stat-value">{n}</span>
          </button>
        ))}
      </div>

      <div className="card overflow-hidden">
        <div className="card-header">
          <div className="relative max-w-xs">
            <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
            <input className="input pl-9" placeholder="Search by email or role…" value={search} onChange={e => setSearch(e.target.value)} />
          </div>
        </div>
        {loading ? (
          <div className="flex justify-center py-16"><Loader2 className="h-6 w-6 animate-spin text-slate-400" /></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead><tr><th>Email</th><th>Role</th><th>Status</th><th>Joined</th><th className="text-right">Actions</th></tr></thead>
              <tbody>
                {filtered.map(u => (
                  <tr key={u.id}>
                    <td className="font-medium text-slate-800">{u.email}</td>
                    <td><RoleCell user={u} onChange={updateRole} /></td>
                    <td>
                      <button onClick={() => toggleActive(u)}
                        className={`inline-flex items-center gap-1.5 text-xs font-medium transition ${u.is_active ? "text-emerald-600 hover:text-emerald-700" : "text-slate-400 hover:text-slate-600"}`}
                        title={u.is_active ? "Click to deactivate" : "Click to activate"}>
                        {u.is_active
                          ? <ToggleRight className="h-4 w-4" />
                          : <ToggleLeft className="h-4 w-4" />}
                        {u.is_active ? "Active" : "Inactive"}
                      </button>
                    </td>
                    <td className="text-xs text-slate-400">{new Date(u.created_at).toLocaleDateString("en-GB")}</td>
                    <td className="text-right">
                      <div className="inline-flex gap-1">
                        <button onClick={() => setResetUser(u)} title="Reset password" className="button-secondary py-1.5 px-2 text-xs"><Key className="h-3.5 w-3.5" /></button>
                        <button onClick={() => deleteUser(u.id)} title="Delete" className="rounded-lg border border-red-200 bg-red-50 px-2 py-1.5 text-xs text-red-600 hover:bg-red-100 transition"><Trash2 className="h-3.5 w-3.5" /></button>
                      </div>
                    </td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr><td colSpan={5} className="py-12 text-center text-slate-400">No users found</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
