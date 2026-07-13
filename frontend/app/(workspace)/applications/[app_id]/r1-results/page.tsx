"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { 
  ArrowLeft, Loader2, User, Briefcase, Mail, Phone, MapPin, 
  CheckCircle2, FileText, Zap, BarChart3, MessageSquare
} from "lucide-react";
import { apiClient } from "@/api/client";

export default function R1ResultsPage() {
  const { app_id } = useParams<{ app_id: string }>();
  const router = useRouter();

  const [loading, setLoading] = useState(true);
  const [candidate, setCandidate] = useState<any>(null);
  const [job, setJob] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadData() {
      try {
        // Fetch candidate details which includes job_id
        const candRes = await apiClient.get(`/admin/candidates/${app_id}`);
        const candData = candRes.data;
        setCandidate(candData);

        // Fetch job details to get the full JD
        if (candData.job_id) {
          const jobRes = await apiClient.get(`/jobs/${candData.job_id}`);
          setJob(jobRes.data);
        }
      } catch (err: any) {
        setError(err.message || "Failed to load results");
      } finally {
        setLoading(false);
      }
    }
    
    if (app_id) {
      loadData();
    }
  }, [app_id]);

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
      </div>
    );
  }

  if (error || !candidate || !job) {
    return (
      <div className="mx-auto max-w-2xl py-20 text-center space-y-4">
        <p className="text-slate-500">{error || "Data not found."}</p>
        <button onClick={() => router.back()} className="button-secondary mx-auto">
          <ArrowLeft className="h-4 w-4" /> Back
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 animate-fade-in pb-20">
      <button onClick={() => router.back()} className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 transition">
        <ArrowLeft className="h-4 w-4" /> Back to Applications
      </button>

      <div className="flex items-center gap-2">
        <BarChart3 className="h-6 w-6 text-brand-600" />
        <h1 className="page-title">R1 Interview Results</h1>
      </div>

      <div className="space-y-6">
        
        {/* Top Row: Candidate and Job Details */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Candidate Details */}
          <div className="card card-body">
            <h2 className="section-label flex items-center gap-2 border-b border-slate-100 pb-3 mb-4">
              <User className="h-4 w-4 text-brand-500" /> Candidate Details
            </h2>
            <div className="space-y-4 text-sm">
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Application ID</p>
                <p className="font-mono text-slate-700 bg-slate-50 p-1.5 rounded inline-block text-xs">{candidate.application_id}</p>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Name</p>
                <p className="font-medium text-slate-800 text-base">{candidate.name}</p>
              </div>
              <div className="flex items-center gap-2 text-slate-600">
                <Mail className="h-4 w-4 text-slate-400" /> {candidate.email}
              </div>
              <div className="flex items-center gap-2 text-slate-600">
                <Phone className="h-4 w-4 text-slate-400" /> {candidate.phone || "—"}
              </div>
              <div className="flex items-center gap-2 text-slate-600">
                <MapPin className="h-4 w-4 text-slate-400" /> {candidate.location || "—"}
              </div>
              <div className="pt-3 border-t border-slate-100">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Role Applied</p>
                <span className="badge-slate text-brand-700 bg-brand-50 border-brand-200">{candidate.job_title}</span>
              </div>
              <div className="pt-3 border-t border-slate-100">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Skills Matched (Pre-Interview)</p>
                <div className="flex flex-wrap gap-1.5">
                  {candidate.matched_skills && candidate.matched_skills.length > 0 ? (
                    candidate.matched_skills.map((skill: string) => (
                      <span key={skill} className="rounded-full bg-emerald-50 border border-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span className="text-slate-400 text-xs">No specific matches</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Job Post Summary */}
          <div className="card card-body">
            <h2 className="section-label flex items-center gap-2 border-b border-slate-100 pb-3 mb-4">
              <Briefcase className="h-4 w-4 text-brand-500" /> Job Post
            </h2>
            <div className="space-y-4">
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Role Name</p>
                <p className="font-medium text-slate-800">{job.title}</p>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Job Description</p>
                <div className="text-xs text-slate-600 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-100 max-h-[300px] overflow-y-auto whitespace-pre-wrap">
                  {job.description}
                </div>
              </div>
            </div>
          </div>
          
        </div>

        {/* Bottom Row: Results Placeholder */}
        <div className="w-full">
          <div className="card card-body min-h-[500px] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-4">
              <h2 className="section-label flex items-center gap-2 text-lg">
                <Zap className="h-5 w-5 text-amber-500" /> R1 Analysis Matrix
              </h2>
              <span className="badge-yellow animate-pulse">Coming Soon</span>
            </div>
            
            <div className="flex-1 flex flex-col items-center justify-center text-center space-y-4 p-8 bg-slate-50/50 rounded-xl border border-dashed border-slate-200">
              <div className="flex gap-4 mb-4">
                <div className="h-16 w-16 bg-white rounded-2xl shadow-sm border border-slate-100 flex items-center justify-center">
                  <MessageSquare className="h-8 w-8 text-blue-500" />
                </div>
                <div className="h-16 w-16 bg-white rounded-2xl shadow-sm border border-slate-100 flex items-center justify-center">
                  <FileText className="h-8 w-8 text-emerald-500" />
                </div>
                <div className="h-16 w-16 bg-white rounded-2xl shadow-sm border border-slate-100 flex items-center justify-center">
                  <BarChart3 className="h-8 w-8 text-brand-500" />
                </div>
              </div>
              <h3 className="text-lg font-bold text-slate-800">Deeper Analysis Engine</h3>
              <p className="text-sm text-slate-500 max-w-md leading-relaxed">
                This panel is ready for the advanced R1 transcript and audio analysis. We will parse the interview data to generate a comprehensive matrix of:
              </p>
              <div className="flex flex-wrap justify-center gap-2 max-w-md pt-2">
                <span className="badge-slate bg-white shadow-sm border border-slate-200 text-slate-700 px-3 py-1">Technical Skills</span>
                <span className="badge-slate bg-white shadow-sm border border-slate-200 text-slate-700 px-3 py-1">Soft Skills</span>
                <span className="badge-slate bg-white shadow-sm border border-slate-200 text-slate-700 px-3 py-1">Communication</span>
                <span className="badge-slate bg-white shadow-sm border border-slate-200 text-slate-700 px-3 py-1">Behavioral Traits</span>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
