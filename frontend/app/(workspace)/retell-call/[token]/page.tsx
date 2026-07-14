"use client";

import { useEffect, useState, useRef } from "react";
import { RetellWebClient } from "retell-client-js-sdk";
import { Mic, PhoneOff, Loader2, Phone, Bot } from "lucide-react";
import { useParams, useRouter } from "next/navigation";

export default function RetellCallPage() {
  const params = useParams();
  const router = useRouter();
  const token = params.token as string;
  
  const [client, setClient] = useState<RetellWebClient | null>(null);
  const [isCalling, setIsCalling] = useState(false);
  const [callEnded, setCallEnded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agentTalking, setAgentTalking] = useState(false);

  useEffect(() => {
    // Initialize the SDK
    const retellClient = new RetellWebClient();
    setClient(retellClient);

    // Setup event listeners
    retellClient.on("call_started", () => {
      console.log("Call started");
      setIsCalling(true);
      setError(null);
    });

    retellClient.on("call_ended", () => {
      console.log("Call ended");
      setIsCalling(false);
      setCallEnded(true);
    });

    retellClient.on("agent_start_talking", () => {
      setAgentTalking(true);
    });

    retellClient.on("agent_stop_talking", () => {
      setAgentTalking(false);
    });

    retellClient.on("error", (err) => {
      console.error("Retell error:", err);
      setError("An error occurred during the call. Please try again.");
      setIsCalling(false);
    });

    return () => {
      retellClient.stopCall();
      retellClient.removeAllListeners();
    };
  }, []);

  async function startCall() {
    if (!client || !token) return;
    try {
      await client.startCall({
        accessToken: token,
      });
    } catch (err: any) {
      console.error("Failed to start call:", err);
      setError(err.message || "Failed to start call. Ensure microphone permissions are granted.");
    }
  }

  function stopCall() {
    if (client) {
      client.stopCall();
    }
  }

  if (callEnded) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-4 animate-fade-in">
        <div className="h-16 w-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mb-2">
          <PhoneOff className="h-8 w-8" />
        </div>
        <h1 className="text-2xl font-bold text-slate-800">Call Ended</h1>
        <p className="text-slate-500 max-w-md">Thank you for your time. The interview recording and transcript will be available to the hiring team shortly.</p>
        <button onClick={() => window.close()} className="button-primary mt-4">
          Close Window
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] max-w-2xl mx-auto space-y-8 animate-fade-in text-center px-4">
      
      <div className="space-y-2">
        <div className="inline-flex items-center justify-center h-12 w-12 rounded-full bg-brand-100 text-brand-600 mb-2">
          <Bot className="h-6 w-6" />
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">AI Interview</h1>
        <p className="text-slate-500">You are about to join an automated interview with our AI recruiter.</p>
      </div>

      <div className={`w-full max-w-md rounded-2xl p-8 border ${isCalling ? 'bg-slate-900 border-slate-800 shadow-2xl shadow-brand-900/20' : 'bg-white border-slate-200 shadow-xl'}`}>
        
        {isCalling ? (
          <div className="flex flex-col items-center space-y-6">
            <div className="relative">
              <div className={`absolute inset-0 rounded-full bg-brand-500/20 animate-ping ${agentTalking ? 'opacity-100' : 'opacity-0'}`}></div>
              <div className="relative h-24 w-24 bg-brand-600 rounded-full flex items-center justify-center shadow-lg shadow-brand-600/30">
                <Mic className="h-10 w-10 text-white" />
              </div>
            </div>
            
            <div className="space-y-1">
              <h2 className="text-lg font-semibold text-white">Call in Progress</h2>
              <p className="text-sm text-slate-400">{agentTalking ? "AI is speaking..." : "Listening..."}</p>
            </div>

            <button 
              onClick={stopCall}
              className="mt-4 flex items-center gap-2 bg-red-500 hover:bg-red-600 text-white px-6 py-3 rounded-full font-semibold transition shadow-lg shadow-red-500/20"
            >
              <PhoneOff className="h-5 w-5" /> End Interview
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center space-y-6">
            <div className="h-24 w-24 bg-slate-100 rounded-full flex items-center justify-center">
              <Phone className="h-10 w-10 text-slate-400" />
            </div>
            
            <div className="space-y-2 text-center w-full">
              <div className="bg-amber-50 border border-amber-200 text-amber-800 text-xs px-4 py-3 rounded-lg text-left">
                <strong>Important:</strong> Please ensure you are in a quiet environment and your browser has microphone permissions enabled.
              </div>
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-600 text-xs px-4 py-3 rounded-lg mt-2">
                  {error}
                </div>
              )}
            </div>

            <button 
              onClick={startCall}
              disabled={!client}
              className="w-full flex justify-center items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white px-6 py-3.5 rounded-xl font-semibold transition shadow-lg shadow-brand-600/20 disabled:opacity-50"
            >
              {!client ? <Loader2 className="h-5 w-5 animate-spin" /> : <Mic className="h-5 w-5" />}
              {client ? "Join Interview" : "Connecting..."}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
