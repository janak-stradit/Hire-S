"use client";

import { useForm } from "react-hook-form";
import { useRouter } from "next/navigation";
import { useState } from "react";
import axios from "axios";
import { Building2, Lock, Mail, ArrowRight, Loader2, ShieldCheck, Users, Zap, Eye, EyeOff, Star } from "lucide-react";
import { apiClient } from "../../api/client";

type LoginForm = { email: string; password: string };

const stats = [
  { value: "10K+", label: "Candidates Screened" },
  { value: "3×",   label: "Faster Time-to-Hire" },
  { value: "98%",  label: "Screening Accuracy"  },
];

const features = [
  { icon: Zap,        title: "AI-Powered Screening",    desc: "Automatically score and rank candidates against JD requirements in seconds.", color: "text-amber-400", bg: "bg-amber-400/10 ring-amber-400/20" },
  { icon: Users,      title: "Talent Pool Management",  desc: "Maintain a reusable pool of pre-screened, ready-to-hire talent.",            color: "text-sky-400",   bg: "bg-sky-400/10   ring-sky-400/20"   },
  { icon: ShieldCheck, title: "Audit & Compliance",     desc: "Every decision is tracked, timestamped and fully explainable.",              color: "text-emerald-400", bg: "bg-emerald-400/10 ring-emerald-400/20" },
];

const testimonial = {
  quote: "HireX cut our screening time from 3 weeks to 4 days. The AI scoring is remarkably consistent.",
  name: "Ananya Mehta", role: "Head of Talent, FinStack Technologies", initials: "AM",
};

function GridPattern() {
  return (
    <svg className="pointer-events-none absolute inset-0 h-full w-full opacity-[0.04]" xmlns="http://www.w3.org/2000/svg">
      <defs><pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
        <path d="M 40 0 L 0 0 0 40" fill="none" stroke="white" strokeWidth="0.8" />
      </pattern></defs>
      <rect width="100%" height="100%" fill="url(#grid)" />
    </svg>
  );
}

export function LoginPage() {
  const router = useRouter();
  const { register, handleSubmit, formState } = useForm<LoginForm>();
  const [error, setError]       = useState("");
  const [showPass, setShowPass] = useState(false);

  async function onSubmit(values: LoginForm) {
    setError("");
    try {
      const res = await apiClient.post("/auth/login", values);
      localStorage.setItem("hirex_token", res.data.access_token);
      const me  = await apiClient.get<{ role: string; email: string }>("/auth/me");
      localStorage.setItem("hirex_role",  me.data.role);
      localStorage.setItem("hirex_email", me.data.email);
      router.push(["admin", "hr", "recruiter"].includes(me.data.role) ? "/operations" : "/jobs");
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 401) setError("Invalid email or password.");
      else setError("Cannot reach the HireX server. Make sure the backend is running.");
    }
  }

  return (
    <div className="flex min-h-screen bg-[#0c1526]">
      {/* Left panel */}
      <div className="relative hidden w-[54%] flex-col overflow-hidden lg:flex">
        <GridPattern />
        <div className="pointer-events-none absolute -top-32 -left-32 h-96 w-96 rounded-full bg-brand-600/20 blur-[96px]" />
        <div className="pointer-events-none absolute bottom-0 right-0 h-72 w-72 rounded-full bg-sky-600/10 blur-[80px]" />
        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-48 bg-gradient-to-t from-[#0c1526] to-transparent" />

        <div className="relative flex h-full flex-col justify-between px-14 py-12">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600 shadow-lg shadow-brand-900/40">
              <Building2 className="h-[22px] w-[22px] text-white" />
            </div>
            <div>
              <p className="text-lg font-extrabold tracking-tight text-white">HireX</p>
              <p className="text-2xs font-semibold uppercase tracking-widest text-slate-500">Talent Operations Platform</p>
            </div>
          </div>

          <div className="space-y-10">
            <div>
              <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-brand-500/30 bg-brand-500/10 px-3.5 py-1.5">
                <Zap className="h-3.5 w-3.5 text-brand-400" />
                <span className="text-xs font-semibold text-brand-300">AI-Powered Recruitment</span>
              </div>
              <h1 className="text-[2.75rem] font-bold leading-[1.15] tracking-tight text-white">
                Hire faster.<br />
                <span className="bg-gradient-to-r from-brand-400 to-sky-400 bg-clip-text text-transparent">Screen smarter.</span>
              </h1>
              <p className="mt-5 max-w-[380px] text-base leading-relaxed text-slate-400">
                Enterprise-grade candidate intelligence. From Naukri sourcing to offer letter — powered by automated validation and AI scoring.
              </p>
            </div>
            <div className="flex gap-4">
              {stats.map(s => (
                <div key={s.label} className="rounded-xl border border-white/[0.08] bg-white/[0.04] px-4 py-3 backdrop-blur-sm">
                  <p className="text-2xl font-bold tracking-tight text-white">{s.value}</p>
                  <p className="mt-0.5 text-xs text-slate-500">{s.label}</p>
                </div>
              ))}
            </div>
            <div className="space-y-4">
              {features.map(({ icon: Icon, title, desc, color, bg }) => (
                <div key={title} className="flex items-start gap-4">
                  <div className={`mt-0.5 flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg ring-1 ${bg}`}>
                    <Icon className={`h-4 w-4 ${color}`} />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-200">{title}</p>
                    <p className="mt-0.5 text-sm leading-relaxed text-slate-500">{desc}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-5 backdrop-blur-sm">
              <div className="mb-3 flex gap-0.5">
                {[...Array(5)].map((_, i) => <Star key={i} className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />)}
              </div>
              <p className="text-sm italic leading-relaxed text-slate-300">&ldquo;{testimonial.quote}&rdquo;</p>
              <div className="mt-4 flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-600/30 text-xs font-bold text-brand-300">{testimonial.initials}</div>
                <div>
                  <p className="text-xs font-semibold text-slate-300">{testimonial.name}</p>
                  <p className="text-2xs text-slate-600">{testimonial.role}</p>
                </div>
              </div>
            </div>
          </div>
          <p className="text-xs text-slate-700">© {new Date().getFullYear()} HireX · Enterprise Talent Operations</p>
        </div>
      </div>

      {/* Right panel */}
      <div className="relative flex flex-1 flex-col items-center justify-center bg-slate-50 px-6 py-12">
        <svg className="pointer-events-none absolute inset-0 h-full w-full opacity-[0.025]" xmlns="http://www.w3.org/2000/svg">
          <defs><pattern id="dots" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.2" fill="#334155" /></pattern></defs>
          <rect width="100%" height="100%" fill="url(#dots)" />
        </svg>

        <div className="relative mb-10 flex items-center gap-3 lg:hidden">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600 shadow-md">
            <Building2 className="h-5 w-5 text-white" />
          </div>
          <span className="text-2xl font-extrabold tracking-tight text-slate-900">HireX</span>
        </div>

        <div className="relative w-full max-w-[420px]">
          <div className="absolute -inset-px rounded-2xl bg-gradient-to-br from-brand-500/20 via-transparent to-sky-500/10 blur-sm" />
          <div className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card-xl">
            <div className="h-1 w-full bg-gradient-to-r from-brand-500 via-sky-500 to-brand-600" />
            <div className="px-8 pt-8 pb-6">
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50 ring-1 ring-brand-200">
                <Building2 className="h-6 w-6 text-brand-600" />
              </div>
              <h2 className="text-2xl font-bold tracking-tight text-slate-900">Welcome back</h2>
              <p className="mt-1.5 text-sm text-slate-500">Sign in to your HireX workspace to continue.</p>
            </div>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5 px-8 pb-8">
              <div className="space-y-1.5">
                <label className="block text-sm font-semibold text-slate-700">Email address</label>
                <div className="relative">
                  <Mail className="pointer-events-none absolute left-3.5 top-1/2 h-[18px] w-[18px] -translate-y-1/2 text-slate-400" />
                  <input type="email" autoComplete="email" placeholder="you@company.com"
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 py-3 pl-10 pr-4 text-sm text-slate-900 shadow-inner-sm placeholder:text-slate-400 outline-none transition focus:border-brand-500 focus:bg-white focus:ring-[3px] focus:ring-brand-500/15"
                    {...register("email", { required: true })} />
                </div>
              </div>
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="block text-sm font-semibold text-slate-700">Password</label>
                  <button type="button" className="text-xs font-medium text-brand-600 hover:underline">Forgot password?</button>
                </div>
                <div className="relative">
                  <Lock className="pointer-events-none absolute left-3.5 top-1/2 h-[18px] w-[18px] -translate-y-1/2 text-slate-400" />
                  <input type={showPass ? "text" : "password"} autoComplete="current-password" placeholder="••••••••"
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 py-3 pl-10 pr-12 text-sm text-slate-900 shadow-inner-sm placeholder:text-slate-400 outline-none transition focus:border-brand-500 focus:bg-white focus:ring-[3px] focus:ring-brand-500/15"
                    {...register("password", { required: true })} />
                  <button type="button" onClick={() => setShowPass(v => !v)}
                    className="absolute inset-y-0 right-0 flex items-center pr-3.5 text-slate-400 hover:text-slate-600 transition-colors" tabIndex={-1}>
                    {showPass ? <EyeOff className="h-[18px] w-[18px]" /> : <Eye className="h-[18px] w-[18px]" />}
                  </button>
                </div>
              </div>
              {error && (
                <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3">
                  <span className="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-red-100 text-xs font-bold text-red-600">!</span>
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              )}
              <button type="submit" disabled={formState.isSubmitting}
                className="group relative mt-2 flex w-full items-center justify-center gap-2.5 overflow-hidden rounded-xl bg-brand-600 px-5 py-3.5 text-sm font-semibold text-white shadow-md transition hover:bg-brand-700 active:scale-[0.98] disabled:opacity-70">
                <span className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/10 to-transparent transition-transform duration-500 group-hover:translate-x-full" />
                {formState.isSubmitting ? <><Loader2 className="h-[18px] w-[18px] animate-spin" /> Signing in…</> : <>Sign in to HireX <ArrowRight className="h-[18px] w-[18px] transition-transform group-hover:translate-x-0.5" /></>}
              </button>
              <div className="flex items-center justify-center gap-4 pt-1">
                <span className="flex items-center gap-1.5 text-xs text-slate-400"><ShieldCheck className="h-3.5 w-3.5" /> 256-bit encrypted</span>
                <span className="h-3.5 w-px bg-slate-200" />
                <span className="flex items-center gap-1.5 text-xs text-slate-400"><ShieldCheck className="h-3.5 w-3.5" /> SOC 2 compliant</span>
              </div>
            </form>
          </div>
          <p className="mt-5 text-center text-xs text-slate-400">Access is restricted to authorised HireX team members.<br />Contact your administrator to request access.</p>
        </div>
      </div>
    </div>
  );
}
