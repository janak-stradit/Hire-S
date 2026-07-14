"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { 
  ArrowLeft, Loader2, User, Briefcase, Mail, Phone, MapPin, 
  CheckCircle2, FileText, Zap, BarChart3, MessageSquare, Database
} from "lucide-react";
import { apiClient } from "@/api/client";

export default function R1ResultsPage() {
  const { app_id } = useParams<{ app_id: string }>();
  const router = useRouter();

  const [loading, setLoading] = useState(true);
  const [candidate, setCandidate] = useState<any>(null);
  const [job, setJob] = useState<any>(null);
  const [error, setError] = useState("");
  const [callData, setCallData] = useState<any>(null);

  useEffect(() => {
    async function loadData() {
      try {
        // Fetch candidate details which includes job_id
        const candRes = await apiClient.get(`/admin/candidates/${app_id}`);
        const candData = candRes.data;
        setCandidate(candData);

        // Fetch job details
        if (candData.job_id) {
          const jobRes = await apiClient.get(`/jobs/${candData.job_id}`);
          setJob(jobRes.data);
        }
        
        // Fetch Call Status once initially
        const callRes = await apiClient.get(`/admin/candidates/${app_id}/agent-status`);
        setCallData(callRes.data);
        
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

  // Polling for call status if not ended
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (callData && callData.status !== "ended" && callData.status !== "none") {
      interval = setInterval(async () => {
        try {
          const callRes = await apiClient.get(`/admin/candidates/${app_id}/agent-status`);
          setCallData(callRes.data);
          if (callRes.data.status === "ended") {
            clearInterval(interval);
          }
        } catch (e) {}
      }, 5000);
    }
    return () => clearInterval(interval);
  }, [callData?.status, app_id]);

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
          {callData?.status === "none" ? (
            <div className="card card-body min-h-[300px] flex flex-col items-center justify-center text-center">
              <MessageSquare className="h-12 w-12 text-slate-300 mb-4" />
              <h3 className="text-lg font-bold text-slate-700">No Interview Found</h3>
              <p className="text-sm text-slate-500 mt-2">This candidate has not had an R1 interview yet.</p>
            </div>
          ) : callData?.status !== "ended" ? (
            <div className="card card-body min-h-[300px] flex flex-col items-center justify-center text-center">
              <Loader2 className="h-12 w-12 text-brand-500 animate-spin mb-4" />
              <h3 className="text-lg font-bold text-slate-700">Interview {callData?.status === "in-progress" ? "In Progress" : "Queued"}</h3>
              <p className="text-sm text-slate-500 mt-2">Waiting for the interview to complete...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
              
              {/* Left Column: Transcript */}
              <div className="lg:col-span-7 card card-body flex flex-col h-[750px]">
                <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-4 shrink-0">
                  <h2 className="section-label flex items-center gap-2 text-lg">
                    <MessageSquare className="h-5 w-5 text-blue-500" /> Full Transcript
                  </h2>
                  <span className="badge-emerald flex items-center gap-1.5 px-3 py-1 text-sm"><CheckCircle2 className="h-4 w-4" /> Interview Completed</span>
                </div>
                
                {callData?.transcript ? (
                  <div className="bg-slate-50 p-5 rounded-xl border border-slate-200 text-sm text-slate-700 whitespace-pre-wrap font-mono leading-relaxed flex-1 overflow-y-auto">
                    {callData.transcript}
                  </div>
                ) : (
                  <div className="flex-1 flex items-center justify-center p-10 text-center text-slate-400">No transcript available</div>
                )}
              </div>

              {/* Right Column: Analysis */}
              <div className="lg:col-span-5 flex flex-col space-y-6 h-[750px]">
                
                {/* Audio Player */}
                {callData?.recording_url && (
                  <div className="card card-body bg-slate-50 border-slate-200 shadow-inner flex flex-col gap-2 shrink-0">
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Audio Recording</p>
                    <audio controls className="w-full" src={callData.recording_url}>
                      Your browser does not support the audio element.
                    </audio>
                  </div>
                )}

                <div className="card card-body flex flex-col flex-1 overflow-hidden">
                  <h2 className="section-label flex items-center gap-2 text-lg border-b border-slate-100 pb-4 mb-4 shrink-0">
                    <Zap className="h-5 w-5 text-brand-500" /> AI Analysis Matrix
                  </h2>

                  <div className="flex-1 overflow-y-auto pr-2 space-y-6">

                  {/* Extracted Data */}
                  {callData?.custom_data && Object.keys(callData.custom_data).length > 0 && (
                    <div className="space-y-3">
                      <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                        <Database className="h-4 w-4 text-purple-500" /> Candidate Data Extracted
                      </h3>
                      <div className="bg-purple-50/50 p-4 rounded-xl border border-purple-100/50 space-y-2">
                        {Object.entries(callData.custom_data).map(([key, value]) => (
                          <div key={key} className="flex flex-col border-b border-purple-100/30 pb-2 last:border-0 last:pb-0">
                            <span className="text-[10px] font-bold text-purple-600/70 uppercase tracking-wider">{key.replace(/_/g, " ")}</span>
                            <span className="text-sm text-slate-800 font-medium">{String(value)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Summary */}
                  {callData?.summary && (
                    <div className="space-y-3">
                      <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2"><FileText className="h-4 w-4 text-emerald-500" /> Executive Summary</h3>
                      <div className="bg-emerald-50/50 p-4 rounded-xl border border-emerald-100/50 text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">
                        {callData.summary}
                      </div>
                    </div>
                  )}

                  </div>

                  {/* Analytics Grid (Retell Only) */}
                  {callData?.provider === "retell" && (
                    <div className="grid grid-cols-2 gap-3 pt-4 mt-4 border-t border-slate-100 shrink-0">
                      <div className="bg-slate-50 border border-slate-100 rounded-lg p-3 flex flex-col text-center">
                        <p className="text-[10px] uppercase font-bold text-slate-400">Duration</p>
                        <p className="text-base font-bold text-slate-800">{callData.duration_ms ? `${Math.round(callData.duration_ms / 1000)}s` : "—"}</p>
                      </div>
                      <div className="bg-slate-50 border border-slate-100 rounded-lg p-3 flex flex-col text-center">
                        <p className="text-[10px] uppercase font-bold text-slate-400">Sentiment</p>
                        <p className="text-base font-bold text-brand-600 capitalize">{callData.user_sentiment || "Neutral"}</p>
                      </div>
                      <div className="bg-slate-50 border border-slate-100 rounded-lg p-3 flex flex-col text-center">
                        <p className="text-[10px] uppercase font-bold text-slate-400">Latency</p>
                        <p className="text-base font-bold text-slate-800">{callData.latency_ms ? `${callData.latency_ms}ms` : "—"}</p>
                      </div>
                      <div className="bg-slate-50 border border-slate-100 rounded-lg p-3 flex flex-col text-center">
                        <p className="text-[10px] uppercase font-bold text-slate-400">Status</p>
                        <p className={`text-xs font-bold mt-1 inline-flex items-center justify-center rounded-full ${callData.call_successful ? "bg-emerald-100 text-emerald-700" : "bg-slate-200 text-slate-600"}`}>
                          {callData.call_successful ? "Successful" : "Ended"}
                        </p>
                      </div>
                    </div>
                  )}
                </div>

              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
