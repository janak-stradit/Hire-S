"use client";

import { useEffect, useState } from "react";
import { ArrowLeft, Save, Loader2, Bot, Mic, Zap, CheckCircle2, Settings2, AudioLines } from "lucide-react";
import { apiClient } from "../../api/client";
import { useRouter } from "next/navigation";

export default function AgentConfigurationPage() {
  const router = useRouter();
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  
  const COST_RATES = {
    transcriber: {
      assemblyai: { cost: 0.003, latency: 90, name: "Assembly AI (English)", engines: ['vapi'] },
      deepgram: { cost: 0.004, latency: 150, name: "Deepgram", engines: ['vapi', 'retell'] },
      talkscriber: { cost: 0.005, latency: 200, name: "Talkscriber", engines: ['vapi'] },
      azure: { cost: 0.005, latency: 530, name: "Azure (Microsoft)", engines: ['retell'] },
      soniox: { cost: 0.006, latency: 490, name: "Soniox", engines: ['retell'] }
    },
    llm: {
      "gpt-5.6-terra": { cost: 0.08, latency: 300, name: "GPT 5.6 Terra", engines: ['vapi', 'retell'] },
      "gpt-5.5": { cost: 0.08, latency: 300, name: "GPT 5.5", engines: ['vapi', 'retell'] },
      "gpt-5.4": { cost: 0.08, latency: 300, name: "GPT 5.4", engines: ['vapi', 'retell'] },
      "gpt-5.2": { cost: 0.056, latency: 250, name: "GPT 5.2", engines: ['vapi', 'retell'] },
      "gpt-5.1": { cost: 0.04, latency: 200, name: "GPT 5.1", engines: ['vapi', 'retell'] },
      "gpt-5": { cost: 0.04, latency: 200, name: "GPT 5", engines: ['vapi', 'retell'] },
      "gpt-5.6-luna": { cost: 0.032, latency: 150, name: "GPT 5.6 Luna", engines: ['vapi', 'retell'] },
      "gpt-5.4-mini": { cost: 0.036, latency: 150, name: "GPT 5.4 mini", engines: ['vapi', 'retell'] },
      "gpt-5.4-nano": { cost: 0.010, latency: 100, name: "GPT 5.4 nano", engines: ['vapi', 'retell'] },
      "gpt-5-mini": { cost: 0.012, latency: 150, name: "GPT 5 mini", engines: ['vapi', 'retell'] },
      "gpt-5-nano": { cost: 0.003, latency: 100, name: "GPT 5 nano", engines: ['vapi', 'retell'] },
      "gpt-4.1-nano": { cost: 0.004, latency: 100, name: "GPT 4.1 nano", engines: ['vapi', 'retell'] },
      "gpt-4.1": { cost: 0.04, latency: 200, name: "GPT 4.1", engines: ['vapi', 'retell'] },
      "claude-5-sonnet": { cost: 0.08, latency: 300, name: "Claude 5 Sonnet", engines: ['vapi', 'retell'] },
      "claude-4.6-sonnet": { cost: 0.08, latency: 300, name: "Claude 4.6 Sonnet", engines: ['vapi', 'retell'] },
      "claude-4.5-sonnet": { cost: 0.08, latency: 300, name: "Claude 4.5 Sonnet", engines: ['vapi', 'retell'] },
      "claude-4.5-haiku": { cost: 0.025, latency: 150, name: "Claude 4.5 Haiku", engines: ['vapi', 'retell'] },
      "gemini-3.5-flash": { cost: 0.081, latency: 250, name: "Gemini 3.5 Flash", engines: ['vapi'] },
      "gemini-3.0-flash": { cost: 0.027, latency: 200, name: "Gemini 3.0 Flash", engines: ['vapi'] },
      "gemini-3.1-flash-lite": { cost: 0.014, latency: 150, name: "Gemini 3.1 Flash Lite", engines: ['vapi'] },
      "gemini-2.5-flash-lite": { cost: 0.006, latency: 120, name: "Gemini 2.5 Flash Lite", engines: ['vapi'] },
      "gpt-realtime-2.1": { cost: 0.38, latency: 100, name: "GPT Realtime 2.1", engines: ['vapi', 'retell'] },
      "gpt-realtime-2": { cost: 0.38, latency: 100, name: "GPT Realtime 2", engines: ['vapi', 'retell'] },
      "gpt-realtime-1.5": { cost: 0.345, latency: 100, name: "GPT Realtime 1.5", engines: ['vapi', 'retell'] },
      "gpt-realtime": { cost: 0.345, latency: 100, name: "GPT Realtime", engines: ['vapi', 'retell'] },
      "gpt-realtime-mini": { cost: 0.07, latency: 100, name: "GPT Realtime mini", engines: ['vapi', 'retell'] },
      "anthropic-bedrock": { cost: 0.00, latency: 0, name: "Anthropic Bedrock (Claude Sonnet 4)", engines: ['vapi', 'retell'] },
      "gpt-4o": { cost: 0.04, latency: 400, name: "OpenAI (GPT-4o)", engines: ['vapi', 'retell'] },
      "anthropic": { cost: 0.03, latency: 350, name: "Anthropic (Claude 3)", engines: ['vapi', 'retell'] },
    },
    voice: {
      "vapi": { cost: 0.02, latency: 250, name: "Vapi (Naina)", engines: ['vapi'] },
      "11labs": { cost: 0.06, latency: 300, name: "11Labs", engines: ['vapi', 'retell'] },
      "cartesia": { cost: 0.03, latency: 200, name: "Cartesia", engines: ['vapi', 'retell'] },
      "openai-Adrian": { cost: 0.03, latency: 250, name: "Adrian (OpenAI)", engines: ['vapi'] },
      "openai-Alloy": { cost: 0.03, latency: 250, name: "Alloy (OpenAI)", engines: ['vapi'] },
      "openai-Andrew": { cost: 0.03, latency: 250, name: "Andrew (Retell)", engines: ['retell'] },
      "openai-Anna": { cost: 0.03, latency: 250, name: "Anna (Retell)", engines: ['retell'] },
      "openai-Ash": { cost: 0.03, latency: 250, name: "Ash (OpenAI)", engines: ['vapi'] },
      "openai-Ballad": { cost: 0.03, latency: 250, name: "Ballad (OpenAI)", engines: ['vapi'] },
      "openai-Brian": { cost: 0.03, latency: 250, name: "Brian (Retell)", engines: ['retell'] },
      "openai-Cedar": { cost: 0.03, latency: 250, name: "Cedar (OpenAI)", engines: ['vapi'] },
      "openai-Chloe": { cost: 0.03, latency: 250, name: "Chloe (Retell)", engines: ['retell'] },
      "openai-Cimo": { cost: 0.03, latency: 250, name: "Cimo (Retell)", engines: ['retell'] },
      "openai-Coral": { cost: 0.03, latency: 250, name: "Coral (OpenAI)", engines: ['vapi'] },
      "openai-Echo": { cost: 0.03, latency: 250, name: "Echo (OpenAI)", engines: ['vapi'] },
      "openai-Emily": { cost: 0.03, latency: 250, name: "Emily (Retell)", engines: ['retell'] },
      "openai-Grace": { cost: 0.03, latency: 250, name: "Grace (Retell)", engines: ['retell'] },
      "openai-Julia": { cost: 0.03, latency: 250, name: "Julia (Retell)", engines: ['retell'] },
      "openai-Kate": { cost: 0.03, latency: 250, name: "Kate (Retell)", engines: ['retell'] },
      "openai-Kathrine": { cost: 0.03, latency: 250, name: "Kathrine (Retell)", engines: ['retell'] },
      "openai-Marin": { cost: 0.03, latency: 250, name: "Marin (OpenAI)", engines: ['vapi'] },
      "openai-Marissa": { cost: 0.03, latency: 250, name: "Marissa (Retell)", engines: ['retell'] },
      "openai-Myra": { cost: 0.03, latency: 250, name: "Myra (Retell)", engines: ['retell'] },
      "openai-Nova": { cost: 0.03, latency: 250, name: "Nova (OpenAI)", engines: ['vapi'] },
      "openai-Onyx": { cost: 0.03, latency: 250, name: "Onyx (OpenAI)", engines: ['vapi'] },
      "openai-Paola": { cost: 0.03, latency: 250, name: "Paola (Retell)", engines: ['retell'] },
      "openai-Sage": { cost: 0.03, latency: 250, name: "Sage (OpenAI)", engines: ['vapi'] },
      "openai-Shimmer": { cost: 0.03, latency: 250, name: "Shimmer (OpenAI)", engines: ['vapi'] },
      "openai-Susan": { cost: 0.03, latency: 250, name: "Susan (Retell)", engines: ['retell'] },
      "openai-Verse": { cost: 0.03, latency: 250, name: "Verse (OpenAI)", engines: ['vapi'] },
      "openai-Zuri": { cost: 0.03, latency: 250, name: "Zuri (Retell)", engines: ['retell'] },
      "openai-Amy": { cost: 0.03, latency: 250, name: "Amy (Retell)", engines: ['retell'] },
      "openai-Anthony": { cost: 0.03, latency: 250, name: "Anthony (Retell)", engines: ['retell'] },
      "openai-Fable": { cost: 0.03, latency: 250, name: "Fable (OpenAI)", engines: ['vapi'] },
      "openai-Santiago": { cost: 0.03, latency: 250, name: "Santiago (Retell)", engines: ['retell'] },
      "openai-Carola": { cost: 0.03, latency: 250, name: "Carola (Retell)", engines: ['retell'] },
      "openai-Monika": { cost: 0.03, latency: 250, name: "Monika (Retell)", engines: ['retell'] },
    }
  };
  
  const [globalSystemPrompt, setGlobalSystemPrompt] = useState("");
  
  // Agent Type
  const [agentProvider, setAgentProvider] = useState("vapi");
  const [firstSpeaker, setFirstSpeaker] = useState("ai");

  // Advanced Retell Settings
  const [retellResponsiveness, setRetellResponsiveness] = useState(1.0);
  const [retellInterruptionSensitivity, setRetellInterruptionSensitivity] = useState(1.0);
  const [retellVoicemailDetection, setRetellVoicemailDetection] = useState(false);
  const [retellIvrHangup, setRetellIvrHangup] = useState(false);
  const [retellEndCallOnSilenceMs, setRetellEndCallOnSilenceMs] = useState(600000);
  const [retellMaxCallDurationMs, setRetellMaxCallDurationMs] = useState(3600000);
  const [retellRingDurationMs, setRetellRingDurationMs] = useState(30000);
  const [retellBoostedKeywords, setRetellBoostedKeywords] = useState("");
  const [retellOptOutSensitiveDataStorage, setRetellOptOutSensitiveDataStorage] = useState(false);
  const [retellFallbackVoiceId, setRetellFallbackVoiceId] = useState("");
  
  // Advanced Transcriber Settings
  const [transcriber, setTranscriber] = useState("assemblyai");
  const [transcriberLanguage, setTranscriberLanguage] = useState("en");
  const [transcriberBackgroundDenoising, setTranscriberBackgroundDenoising] = useState(false);
  const [transcriberConfidenceThreshold, setTranscriberConfidenceThreshold] = useState(1.0);
  const [transcriberKeyterms, setTranscriberKeyterms] = useState("");
  const [transcriberEndOfTurnConfidence, setTranscriberEndOfTurnConfidence] = useState(1.0);
  const [transcriberMinEndOfTurnSilence, setTranscriberMinEndOfTurnSilence] = useState(160);
  const [transcriberMaxTurnSilence, setTranscriberMaxTurnSilence] = useState(400);
  const [transcriberSmartEndpointing, setTranscriberSmartEndpointing] = useState(false);
  const [transcriberFallbackProvider, setTranscriberFallbackProvider] = useState("deepgram");
  const [transcriberFallbackLanguage, setTranscriberFallbackLanguage] = useState("en");
  const [transcriberFallbackModel, setTranscriberFallbackModel] = useState("nova-2-general");

  // Advanced LLM Settings
  const [llmModel, setLlmModel] = useState("anthropic-bedrock");
  const [llmTemperature, setLlmTemperature] = useState(0.7);
  const [llmMaxTokens, setLlmMaxTokens] = useState(250);
  const [llmEmotionRecognitionEnabled, setLlmEmotionRecognitionEnabled] = useState(false);
  const [llmNumFastTurns, setLlmNumFastTurns] = useState(1);

  // Advanced Voice Settings
  const [voiceProvider, setVoiceProvider] = useState("vapi");
  const [voiceSpeed, setVoiceSpeed] = useState(1.0);
  const [voiceStability, setVoiceStability] = useState(0.5);
  const [voiceSimilarityBoost, setVoiceSimilarityBoost] = useState(0.75);
  const [voiceOptimizeStreamingLatency, setVoiceOptimizeStreamingLatency] = useState(3);
  const [voiceFillerInjectionEnabled, setVoiceFillerInjectionEnabled] = useState(false);
  const [voiceBackgroundSound, setVoiceBackgroundSound] = useState("off");

  // Job selection
  const [jobs, setJobs] = useState<{id: string, title: string, agent_prompt: string | null}[]>([]);
  const [promptType, setPromptType] = useState<"default" | "role">("default");
  const [selectedJobId, setSelectedJobId] = useState("");
  const [jobPrompts, setJobPrompts] = useState<Record<string, string>>({});

  useEffect(() => {
    if (promptType === "default") {
      setSelectedJobId("");
    } else if (promptType === "role" && jobs.length > 0 && !selectedJobId) {
      setSelectedJobId(jobs[0].id);
    }
  }, [promptType, jobs, selectedJobId]);

  useEffect(() => {
    Promise.all([
      apiClient.get("/admin/agent-config"),
      apiClient.get("/admin/agent-config/jobs")
    ])
      .then(([configRes, jobsRes]) => {
        const config = configRes.data;
        setGlobalSystemPrompt(config.system_prompt || "");
        
        setAgentProvider(config.agent_provider || "vapi");
        setFirstSpeaker(config.first_speaker || "ai");

        // Retell
        setRetellResponsiveness(config.retell_responsiveness ?? 1.0);
        setRetellInterruptionSensitivity(config.retell_interruption_sensitivity ?? 1.0);
        setRetellVoicemailDetection(config.retell_voicemail_detection || false);
        setRetellIvrHangup(config.retell_ivr_hangup || false);
        setRetellEndCallOnSilenceMs(config.retell_end_call_on_silence_ms ?? 600000);
        setRetellMaxCallDurationMs(config.retell_max_call_duration_ms ?? 3600000);
        setRetellRingDurationMs(config.retell_ring_duration_ms ?? 30000);
        setRetellBoostedKeywords(config.retell_boosted_keywords || "");
        setRetellOptOutSensitiveDataStorage(config.retell_opt_out_sensitive_data_storage || false);
        setRetellFallbackVoiceId(config.retell_fallback_voice_id || "");

        // Transcriber
        setTranscriber(config.transcriber_model || "assemblyai");
        setTranscriberLanguage(config.transcriber_language || "en");
        setTranscriberBackgroundDenoising(config.transcriber_background_denoising || false);
        setTranscriberConfidenceThreshold(config.transcriber_confidence_threshold ?? 1.0);
        setTranscriberKeyterms(config.transcriber_keyterms || "");
        setTranscriberEndOfTurnConfidence(config.transcriber_end_of_turn_confidence ?? 1.0);
        setTranscriberMinEndOfTurnSilence(config.transcriber_min_end_of_turn_silence ?? 160);
        setTranscriberMaxTurnSilence(config.transcriber_max_turn_silence ?? 400);
        setTranscriberSmartEndpointing(config.transcriber_smart_endpointing || false);
        setTranscriberFallbackProvider(config.transcriber_fallback_provider || "deepgram");
        setTranscriberFallbackLanguage(config.transcriber_fallback_language || "en");
        setTranscriberFallbackModel(config.transcriber_fallback_model || "nova-2-general");

        // LLM
        setLlmModel(config.llm_model || "anthropic-bedrock");
        setLlmTemperature(config.llm_temperature ?? 0.7);
        setLlmMaxTokens(config.llm_max_tokens ?? 250);
        setLlmEmotionRecognitionEnabled(config.llm_emotion_recognition_enabled || false);
        setLlmNumFastTurns(config.llm_num_fast_turns ?? 1);

        // Voice
        setVoiceProvider(config.voice_provider || "vapi");
        setVoiceSpeed(config.voice_speed ?? 1.0);
        setVoiceStability(config.voice_stability ?? 0.5);
        setVoiceSimilarityBoost(config.voice_similarity_boost ?? 0.75);
        setVoiceOptimizeStreamingLatency(config.voice_optimize_streaming_latency ?? 3);
        setVoiceFillerInjectionEnabled(config.voice_filler_injection_enabled || false);
        setVoiceBackgroundSound(config.voice_background_sound || "off");

        console.log("Config:", configRes.data);
        console.log("Jobs:", jobsRes.data);
        setJobs(jobsRes.data);
        
        const initialJobPrompts: Record<string, string> = {};
        jobsRes.data.forEach((j: any) => {
          if (j.agent_prompt) initialJobPrompts[j.id] = j.agent_prompt;
        });
        setJobPrompts(initialJobPrompts);
      })
      .catch((err) => {
        console.error("Fetch error:", err);
        alert("Failed to load configuration: " + err?.message);
      })
      .finally(() => setLoading(false));
  }, []);

  async function handleSave() {
    setSaving(true);
    setSaveSuccess(false);
    try {
      await apiClient.put("/admin/agent-config", {
        agent_provider: agentProvider,
        first_speaker: firstSpeaker,
        system_prompt: globalSystemPrompt,
        
        retell_responsiveness: retellResponsiveness,
        retell_interruption_sensitivity: retellInterruptionSensitivity,
        retell_voicemail_detection: retellVoicemailDetection,
        retell_ivr_hangup: retellIvrHangup,
        retell_end_call_on_silence_ms: retellEndCallOnSilenceMs,
        retell_max_call_duration_ms: retellMaxCallDurationMs,
        retell_ring_duration_ms: retellRingDurationMs,
        retell_boosted_keywords: retellBoostedKeywords,
        retell_opt_out_sensitive_data_storage: retellOptOutSensitiveDataStorage,
        retell_fallback_voice_id: retellFallbackVoiceId,

        transcriber_model: transcriber,
        transcriber_language: transcriberLanguage,
        transcriber_background_denoising: transcriberBackgroundDenoising,
        transcriber_confidence_threshold: transcriberConfidenceThreshold,
        transcriber_keyterms: transcriberKeyterms,
        transcriber_end_of_turn_confidence: transcriberEndOfTurnConfidence,
        transcriber_min_end_of_turn_silence: transcriberMinEndOfTurnSilence,
        transcriber_max_turn_silence: transcriberMaxTurnSilence,
        transcriber_smart_endpointing: transcriberSmartEndpointing,
        transcriber_fallback_provider: transcriberFallbackProvider,
        transcriber_fallback_language: transcriberFallbackLanguage,
        transcriber_fallback_model: transcriberFallbackModel,

        llm_model: llmModel,
        llm_temperature: llmTemperature,
        llm_max_tokens: llmMaxTokens,
        llm_emotion_recognition_enabled: llmEmotionRecognitionEnabled,
        llm_num_fast_turns: llmNumFastTurns,

        voice_provider: voiceProvider,
        voice_speed: voiceSpeed,
        voice_stability: voiceStability,
        voice_similarity_boost: voiceSimilarityBoost,
        voice_optimize_streaming_latency: voiceOptimizeStreamingLatency,
        voice_filler_injection_enabled: voiceFillerInjectionEnabled,
        voice_background_sound: voiceBackgroundSound,
      });

      if (selectedJobId) {
        await apiClient.put(`/admin/agent-config/jobs/${selectedJobId}/prompt`, {
          agent_prompt: jobPrompts[selectedJobId] || ""
        });
      }

      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      alert("Failed to save configuration");
    } finally {
      setSaving(false);
    }
  }

  const currentPromptValue = selectedJobId ? (jobPrompts[selectedJobId] ?? "") : globalSystemPrompt;

  const handlePromptChange = (val: string) => {
    if (selectedJobId) {
      setJobPrompts(prev => ({ ...prev, [selectedJobId]: val }));
    } else {
      setGlobalSystemPrompt(val);
    }
  };

  if (loading) {
    return <div className="flex justify-center py-20"><Loader2 className="h-6 w-6 animate-spin text-slate-400" /></div>;
  }

  const currentTranscriber = COST_RATES.transcriber[transcriber as keyof typeof COST_RATES.transcriber] || { cost: 0.005, latency: 150, name: transcriber };
  const currentLlm = COST_RATES.llm[llmModel as keyof typeof COST_RATES.llm] || { cost: 0.02, latency: 300, name: llmModel };
  const currentVoice = COST_RATES.voice[voiceProvider as keyof typeof COST_RATES.voice] || { cost: 0.04, latency: 250, name: voiceProvider };

  const totalCost = currentTranscriber.cost + currentLlm.cost + currentVoice.cost;
  const totalLatency = currentTranscriber.latency + currentLlm.latency + currentVoice.latency;

  return (
    <div className="mx-auto max-w-[1400px] space-y-6 animate-fade-in pb-20">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <button onClick={() => router.push("/operations")} className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 transition mb-2">
            <ArrowLeft className="h-4 w-4" /> Back to Operations
          </button>
          <h1 className="page-title flex items-center gap-2">
            <Bot className="h-6 w-6 text-brand-600" /> AI Interviewer Configuration
          </h1>
          <p className="page-subtitle mt-1">Configure advanced settings for Transcriber, Language Model, and Voice Provider.</p>
        </div>
        <div className="flex items-center gap-3">
          {saveSuccess && <span className="text-sm font-medium text-emerald-600 flex items-center gap-1"><CheckCircle2 className="h-4 w-4" /> Saved successfully</span>}
          <button onClick={handleSave} disabled={saving} className="button-primary">
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} Save Configuration
          </button>
        </div>
      </div>

      <div className="space-y-6">
        
        {/* Top Controls: Choose Agent Dropdown */}
        <div className="flex justify-end mb-4 relative z-20">
          <div className="flex items-center gap-3">
            <label className="text-sm font-semibold text-slate-700">Choose Agent Engine</label>
            <select 
              value={agentProvider} 
              onChange={e => setAgentProvider(e.target.value)} 
              className="input text-sm py-2 px-4 w-48 shadow-sm"
            >
              <option value="vapi">Vapi Engine</option>
              <option value="retell">Retell AI Engine</option>
            </select>
          </div>
        </div>

        {/* Cost Estimator Banner */}
        <div className="bg-slate-900 rounded-xl p-5 lg:p-6 text-white shadow-xl shadow-brand-900/10 flex flex-col xl:flex-row justify-between items-start xl:items-center gap-6 border border-slate-800 relative overflow-hidden">
          {/* Subtle background glow effect */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-brand-500/10 rounded-full blur-[80px] pointer-events-none transform translate-x-1/2 -translate-y-1/2"></div>
          
          <div className="flex flex-col sm:flex-row gap-6 sm:gap-12 w-full xl:w-auto relative z-10">
            <div>
              <p className="text-slate-400 text-xs font-semibold tracking-wider uppercase mb-1 flex items-center gap-1.5"><Zap className="h-3.5 w-3.5" /> Average Cost</p>
              <div className="text-4xl font-bold text-emerald-400 tracking-tight">~${totalCost.toFixed(3)}<span className="text-sm font-medium text-emerald-400/60 ml-1">/min</span></div>
            </div>
            <div className="hidden sm:block w-px h-12 bg-slate-800 self-center"></div>
            <div>
              <p className="text-slate-400 text-xs font-semibold tracking-wider uppercase mb-1 flex items-center gap-1.5"><Zap className="h-3.5 w-3.5" /> Average Latency</p>
              <div className="text-4xl font-bold text-amber-400 tracking-tight">~{totalLatency}<span className="text-sm font-medium text-amber-400/60 ml-1">ms</span></div>
            </div>
          </div>
          
          <div className="flex flex-col sm:flex-row w-full xl:w-auto gap-3 text-xs relative z-10">
            <div className="flex-1 xl:w-48 bg-slate-800/60 backdrop-blur-md rounded-lg p-3.5 border border-slate-700/50 shadow-inner">
              <p className="text-slate-400 font-semibold mb-1.5 uppercase tracking-wider text-[10px]">Transcriber</p>
              <p className="font-medium text-slate-100 text-sm truncate" title={currentTranscriber.name}>{currentTranscriber.name}</p>
              <p className="text-emerald-400/90 mt-1 font-mono">${currentTranscriber.cost.toFixed(3)}/min <span className="text-slate-500 mx-1">•</span> <span className="text-amber-400/90">{currentTranscriber.latency}ms</span></p>
            </div>
            <div className="flex-1 xl:w-48 bg-slate-800/60 backdrop-blur-md rounded-lg p-3.5 border border-slate-700/50 shadow-inner">
              <p className="text-slate-400 font-semibold mb-1.5 uppercase tracking-wider text-[10px]">Model</p>
              <p className="font-medium text-slate-100 text-sm truncate" title={currentLlm.name}>{currentLlm.name}</p>
              <p className="text-emerald-400/90 mt-1 font-mono">${currentLlm.cost.toFixed(3)}/min <span className="text-slate-500 mx-1">•</span> <span className="text-amber-400/90">{currentLlm.latency}ms</span></p>
            </div>
            <div className="flex-1 xl:w-48 bg-slate-800/60 backdrop-blur-md rounded-lg p-3.5 border border-slate-700/50 shadow-inner">
              <p className="text-slate-400 font-semibold mb-1.5 uppercase tracking-wider text-[10px]">Voice</p>
              <p className="font-medium text-slate-100 text-sm truncate" title={currentVoice.name}>{currentVoice.name}</p>
              <p className="text-emerald-400/90 mt-1 font-mono">${currentVoice.cost.toFixed(3)}/min <span className="text-slate-500 mx-1">•</span> <span className="text-amber-400/90">{currentVoice.latency}ms</span></p>
            </div>
          </div>
        </div>

        {/* Top Section: Models, Voices, and Transcriber */}
        <div className={`grid grid-cols-1 md:grid-cols-2 ${agentProvider === 'retell' ? 'xl:grid-cols-4' : 'lg:grid-cols-3'} gap-4`}>
          
          {/* Advanced Transcriber Settings */}
          <div className="card p-3 space-y-3 h-full shadow-sm">
            <h2 className="section-label flex items-center gap-2 border-b border-slate-100 pb-2 text-xs font-bold uppercase tracking-wider">
              <Mic className="h-3.5 w-3.5 text-brand-500" /> Transcriber
            </h2>
            
            <div className="space-y-2">
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-700">Provider</label>
                  <select value={transcriber} onChange={e => setTranscriber(e.target.value)} className="input text-xs py-1 px-2">
                    {Object.entries(COST_RATES.transcriber)
                      .filter(([_, data]) => data.engines.includes(agentProvider))
                      .map(([key, data]) => (
                        <option key={key} value={key}>{data.name}</option>
                      ))}
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-700">Language</label>
                  <select value={transcriberLanguage} onChange={e => setTranscriberLanguage(e.target.value)} className="input text-xs py-1 px-2">
                    <option value="auto">Auto-detect / Multilingual</option>
                    <option value="en-US">English (US)</option>
                    <option value="en-IN">English (India)</option>
                    <option value="en-GB">English (UK)</option>
                    <option value="en-AU">English (Australia)</option>
                    <option value="es-ES">Spanish (Spain)</option>
                    <option value="es-419">Spanish (Latin America)</option>
                    <option value="fr-FR">French (France)</option>
                    <option value="fr-CA">French (Canada)</option>
                    <option value="hi-IN">Hindi (India)</option>
                    <option value="de-DE">German (Germany)</option>
                    <option value="ja-JP">Japanese</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-slate-700 flex justify-between">
                  <span>Confidence Threshold</span>
                  <span className="text-slate-500">{transcriberConfidenceThreshold.toFixed(2)}</span>
                </label>
                <input type="range" min="0" max="1" step="0.05" value={transcriberConfidenceThreshold} onChange={e => setTranscriberConfidenceThreshold(parseFloat(e.target.value))} className="w-full accent-brand-600 h-1.5" />
              </div>

              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-slate-700 flex justify-between">
                  <span>EOT Confidence</span>
                  <span className="text-slate-500">{transcriberEndOfTurnConfidence.toFixed(2)}</span>
                </label>
                <input type="range" min="0" max="1" step="0.05" value={transcriberEndOfTurnConfidence} onChange={e => setTranscriberEndOfTurnConfidence(parseFloat(e.target.value))} className="w-full accent-brand-600 h-1.5" />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <label className="text-[10px] font-semibold text-slate-700 uppercase">Min EOT Silence (ms)</label>
                  <input type="number" value={transcriberMinEndOfTurnSilence} onChange={e => setTranscriberMinEndOfTurnSilence(parseInt(e.target.value) || 0)} className="input text-xs py-1 px-2" />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-semibold text-slate-700 uppercase">Max Turn Silence (ms)</label>
                  <input type="number" value={transcriberMaxTurnSilence} onChange={e => setTranscriberMaxTurnSilence(parseInt(e.target.value) || 0)} className="input text-xs py-1 px-2" />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-slate-700">Keyterms Prompt</label>
                <input type="text" value={transcriberKeyterms} onChange={e => setTranscriberKeyterms(e.target.value)} placeholder="e.g. Vapi, API" className="input text-xs py-1 px-2" />
              </div>

              <div className="flex flex-col gap-1.5 pt-1">
                <label className="flex items-center gap-2 text-xs text-slate-700">
                  <input type="checkbox" checked={transcriberBackgroundDenoising} onChange={e => setTranscriberBackgroundDenoising(e.target.checked)} className="rounded text-brand-600 focus:ring-brand-500 h-3 w-3" />
                  Enable Background Denoising
                </label>
                <label className="flex items-center gap-2 text-xs text-slate-700">
                  <input type="checkbox" checked={transcriberSmartEndpointing} onChange={e => setTranscriberSmartEndpointing(e.target.checked)} className="rounded text-brand-600 focus:ring-brand-500 h-3 w-3" />
                  Enable Smart Endpointing
                </label>
              </div>

              <div className="pt-3 border-t border-slate-100">
                <h3 className="text-[10px] font-semibold text-slate-500 mb-2 uppercase tracking-wider">Fallback Settings</h3>
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <label className="text-[10px] font-medium text-slate-600">Provider</label>
                    <select value={transcriberFallbackProvider} onChange={e => setTranscriberFallbackProvider(e.target.value)} className="input text-xs py-1 px-2">
                      {Object.entries(COST_RATES.transcriber)
                        .filter(([_, data]) => data.engines.includes(agentProvider))
                        .map(([key, data]) => (
                          <option key={key} value={key}>{data.name}</option>
                        ))}
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-medium text-slate-600">Model</label>
                    <input type="text" value={transcriberFallbackModel} onChange={e => setTranscriberFallbackModel(e.target.value)} className="input text-xs py-1 px-2" />
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Advanced Language Model Settings */}
          <div className="card p-3 space-y-3 h-full shadow-sm">
            <h2 className="section-label flex items-center gap-2 border-b border-slate-100 pb-2 text-xs font-bold uppercase tracking-wider">
              <Zap className="h-3.5 w-3.5 text-brand-500" /> Language Model (LLM)
            </h2>
            
            <div className="space-y-2">
              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-slate-700">Model</label>
                <select value={llmModel} onChange={e => setLlmModel(e.target.value)} className="input text-xs py-1 px-2">
                  {Object.entries(COST_RATES.llm)
                    .filter(([_, data]) => data.engines.includes(agentProvider))
                    .map(([key, data]) => (
                    <option key={key} value={key}>{data.name} (${data.cost}/min)</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-slate-700 flex justify-between">
                  <span>Temperature</span>
                  <span className="text-slate-500">{llmTemperature.toFixed(2)}</span>
                </label>
                <input type="range" min="0" max="2" step="0.05" value={llmTemperature} onChange={e => setLlmTemperature(parseFloat(e.target.value))} className="w-full accent-brand-600 h-1.5" />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <label className="text-[10px] font-semibold text-slate-700 uppercase">Max Tokens</label>
                  <input type="number" value={llmMaxTokens} onChange={e => setLlmMaxTokens(parseInt(e.target.value) || 0)} className="input text-xs py-1 px-2" />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-semibold text-slate-700 uppercase">Fast Turns (Count)</label>
                  <input type="number" value={llmNumFastTurns} onChange={e => setLlmNumFastTurns(parseInt(e.target.value) || 0)} className="input text-xs py-1 px-2" />
                </div>
              </div>

              <div className="pt-2">
                <label className="flex items-center gap-2 text-xs text-slate-700">
                  <input type="checkbox" checked={llmEmotionRecognitionEnabled} onChange={e => setLlmEmotionRecognitionEnabled(e.target.checked)} className="rounded text-brand-600 focus:ring-brand-500 h-3 w-3" />
                  Enable Emotion Recognition
                </label>
              </div>
            </div>
            
            <div className="rounded-lg bg-blue-50 p-2.5 border border-blue-100 mt-auto">
              <p className="text-[10px] text-blue-800 leading-tight">
                <strong>Tip:</strong> Bedrock offers the best logic/latency tradeoff.
              </p>
            </div>
          </div>

          {/* Advanced Voice Settings */}
          <div className="card p-3 space-y-3 h-full shadow-sm">
            <h2 className="section-label flex items-center gap-2 border-b border-slate-100 pb-2 text-xs font-bold uppercase tracking-wider">
              <AudioLines className="h-3.5 w-3.5 text-brand-500" /> Voice Settings
            </h2>
            
            <div className="space-y-2">
              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-slate-700">Voice Provider</label>
                <select value={voiceProvider} onChange={e => setVoiceProvider(e.target.value)} className="input text-xs py-1 px-2">
                  {Object.entries(COST_RATES.voice)
                    .filter(([_, data]) => data.engines.includes(agentProvider))
                    .map(([key, data]) => (
                    <option key={key} value={key}>{data.name}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-slate-700 flex justify-between">
                  <span>Speed</span>
                  <span className="text-slate-500">{voiceSpeed.toFixed(2)}x</span>
                </label>
                <input type="range" min="0.5" max="2" step="0.05" value={voiceSpeed} onChange={e => setVoiceSpeed(parseFloat(e.target.value))} className="w-full accent-brand-600 h-1.5" />
              </div>

              {voiceProvider === '11labs' && (
                <>
                  <div className="space-y-1">
                    <label className="text-[11px] font-semibold text-slate-700 flex justify-between">
                      <span>Stability</span>
                      <span className="text-slate-500">{voiceStability.toFixed(2)}</span>
                    </label>
                    <input type="range" min="0" max="1" step="0.05" value={voiceStability} onChange={e => setVoiceStability(parseFloat(e.target.value))} className="w-full accent-brand-600 h-1.5" />
                  </div>

                  <div className="space-y-1">
                    <label className="text-[11px] font-semibold text-slate-700 flex justify-between">
                      <span>Similarity Boost</span>
                      <span className="text-slate-500">{voiceSimilarityBoost.toFixed(2)}</span>
                    </label>
                    <input type="range" min="0" max="1" step="0.05" value={voiceSimilarityBoost} onChange={e => setVoiceSimilarityBoost(parseFloat(e.target.value))} className="w-full accent-brand-600 h-1.5" />
                  </div>
                </>
              )}

              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-slate-700">Latency Optimization</label>
                <select value={voiceOptimizeStreamingLatency} onChange={e => setVoiceOptimizeStreamingLatency(parseInt(e.target.value))} className="input text-xs py-1 px-2">
                  <option value={0}>0 - Default</option>
                  <option value={1}>1 - Normal</option>
                  <option value={2}>2 - Strong</option>
                  <option value={3}>3 - Max</option>
                  <option value={4}>4 - Extreme</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-1">
                <div className="flex flex-col gap-1">
                  <label className="flex items-center gap-2 text-xs text-slate-700 mt-4">
                    <input type="checkbox" checked={voiceFillerInjectionEnabled} onChange={e => setVoiceFillerInjectionEnabled(e.target.checked)} className="rounded text-brand-600 focus:ring-brand-500 h-3 w-3" />
                    Filler Injection
                  </label>
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] font-semibold text-slate-700 uppercase">Background Sound</label>
                  <select value={voiceBackgroundSound} onChange={e => setVoiceBackgroundSound(e.target.value)} className="input text-xs py-1 px-2">
                    <option value="off">Off</option>
                    <option value="office">Office</option>
                    <option value="cafe">Cafe</option>
                  </select>
                </div>
              </div>

            </div>
          </div>
          
          {agentProvider === 'retell' && (
            <div className="card p-3 space-y-3 h-full shadow-sm">
              <h2 className="section-label flex items-center gap-2 border-b border-slate-100 pb-2 text-xs font-bold uppercase tracking-wider">
                <Bot className="h-3.5 w-3.5 text-brand-500" /> Retell Options
              </h2>
              <div className="space-y-2">
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-700">Responsiveness ({retellResponsiveness})</label>
                  <input type="range" min="0" max="2" step="0.1" value={retellResponsiveness} onChange={e => setRetellResponsiveness(parseFloat(e.target.value))} className="w-full accent-brand-600 h-1.5" />
                </div>
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-700">Interruption Sensitivity ({retellInterruptionSensitivity})</label>
                  <input type="range" min="0" max="2" step="0.1" value={retellInterruptionSensitivity} onChange={e => setRetellInterruptionSensitivity(parseFloat(e.target.value))} className="w-full accent-brand-600 h-1.5" />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <label className="text-[10px] font-semibold text-slate-700 uppercase">Ring (ms)</label>
                    <input type="number" value={retellRingDurationMs} onChange={e => setRetellRingDurationMs(parseInt(e.target.value) || 0)} className="input text-xs py-1 px-2" />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-semibold text-slate-700 uppercase">Max Call (ms)</label>
                    <input type="number" value={retellMaxCallDurationMs} onChange={e => setRetellMaxCallDurationMs(parseInt(e.target.value) || 0)} className="input text-xs py-1 px-2" />
                  </div>
                </div>
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-700">End Call on Silence (ms)</label>
                  <input type="number" value={retellEndCallOnSilenceMs} onChange={e => setRetellEndCallOnSilenceMs(parseInt(e.target.value) || 0)} className="input text-xs py-1 px-2" />
                </div>
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-700">Boosted Keywords</label>
                  <input type="text" value={retellBoostedKeywords} onChange={e => setRetellBoostedKeywords(e.target.value)} placeholder="comma, separated" className="input text-xs py-1 px-2" />
                </div>
                <div className="flex flex-col gap-1.5 pt-2 border-t border-slate-100">
                  <label className="flex items-center gap-2 text-[11px] text-slate-700">
                    <input type="checkbox" checked={retellVoicemailDetection} onChange={e => setRetellVoicemailDetection(e.target.checked)} className="rounded text-brand-600 focus:ring-brand-500 h-3 w-3" />
                    Detect Voicemail
                  </label>
                  <label className="flex items-center gap-2 text-[11px] text-slate-700">
                    <input type="checkbox" checked={retellIvrHangup} onChange={e => setRetellIvrHangup(e.target.checked)} className="rounded text-brand-600 focus:ring-brand-500 h-3 w-3" />
                    Hangup on IVR
                  </label>
                  <label className="flex items-center gap-2 text-[11px] text-slate-700">
                    <input type="checkbox" checked={retellOptOutSensitiveDataStorage} onChange={e => setRetellOptOutSensitiveDataStorage(e.target.checked)} className="rounded text-brand-600 focus:ring-brand-500 h-3 w-3" />
                    Opt-out of PII Data Storage
                  </label>
                </div>
                <div className="pt-2 border-t border-slate-100">
                    <label className="text-[11px] font-semibold text-slate-700">Fallback Voice ID (Optional)</label>
                    <input type="text" value={retellFallbackVoiceId} onChange={e => setRetellFallbackVoiceId(e.target.value)} placeholder="e.g. openai-Alloy" className="input text-xs py-1 px-2 mt-1" />
                </div>
              </div>
            </div>
          )}
        </div>
        
        {/* Bottom Section: Prompt & Variables */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Left Column: Editor */}
          <div className="lg:col-span-2 space-y-5">
            <div className="card overflow-hidden flex flex-col h-full min-h-[500px]">
              <div className="card-header border-b border-slate-100 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h2 className="section-label flex items-center gap-2">System Prompt Instructions</h2>
                  <p className="text-xs text-slate-500 mt-1">This is the persona and script the AI will follow during the call.</p>
                </div>
                
                <div className="flex flex-col sm:flex-row gap-3 sm:items-center">
                  <div className="flex flex-col gap-1">
                    <label className="text-xs font-semibold text-slate-700">First Speaker</label>
                    <select 
                      value={firstSpeaker} 
                      onChange={e => setFirstSpeaker(e.target.value)} 
                      className="input text-sm py-1.5 px-3 bg-white border-slate-200 w-40"
                    >
                      <option value="ai">AI speaks first</option>
                      <option value="user">User speaks first</option>
                      <option value="dynamic">Dynamic message</option>
                    </select>
                  </div>
                  
                  <div className="flex flex-col gap-1">
                    <label className="text-xs font-semibold text-slate-700">Prompt Type</label>
                    <select 
                      value={promptType} 
                      onChange={e => setPromptType(e.target.value as "default" | "role")} 
                      className="input text-sm py-1.5 px-3 bg-white border-slate-200 w-40"
                    >
                      <option value="default">Default</option>
                      <option value="role">Role Based</option>
                    </select>
                  </div>
                  
                  {promptType === "role" && (
                    <div className="flex flex-col gap-1">
                      <label className="text-xs font-semibold text-slate-700">Choose Role</label>
                      <select 
                        value={selectedJobId} 
                        onChange={e => setSelectedJobId(e.target.value)} 
                        className="input text-sm py-1.5 px-3 bg-white border-slate-200 w-56"
                      >
                        {jobs.length === 0 && <option value="">No roles available</option>}
                        {jobs.map(job => (
                          <option key={job.id} value={job.id}>
                            {job.title} {jobPrompts[job.id] ? " (Customized)" : ""}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}
                </div>
              </div>
              <div className="p-0 flex-1 flex flex-col relative">
                {selectedJobId && !jobPrompts[selectedJobId] && (
                  <div className="absolute top-4 right-4 bg-blue-50 border border-blue-200 text-blue-700 text-xs px-3 py-1.5 rounded-md shadow-sm">
                    Editing override for <strong>{jobs.find(j => j.id === selectedJobId)?.title}</strong>. Leave empty to fallback to Default.
                  </div>
                )}
                <textarea
                  value={currentPromptValue}
                  onChange={e => handlePromptChange(e.target.value)}
                  className="w-full flex-1 p-5 text-sm font-mono text-slate-300 bg-slate-900 focus:outline-none resize-none leading-relaxed min-h-[400px]"
                  placeholder={selectedJobId ? `Type custom prompt for this role (or it will use the Global Default):\n\n${globalSystemPrompt}` : "Enter the global AI instructions..."}
                  spellCheck={false}
                />
              </div>
            </div>
          </div>
          
          {/* Variables Guide */}
          <div className="card card-body space-y-4">
            <h2 className="section-label flex items-center gap-2 border-b border-slate-100 pb-3">Dynamic Variables</h2>
            <p className="text-xs text-slate-500">You can inject candidate details into the prompt using Handlebars syntax. These will be replaced automatically when the call is scheduled.</p>
            
            <div className="space-y-3">
              <div className="text-sm">
                <code className="text-xs font-semibold text-brand-600 bg-brand-50 px-1.5 py-0.5 rounded">{"{{candidate.name}}"}</code>
                <p className="text-xs text-slate-500 mt-0.5">Candidate's full name</p>
              </div>
              <div className="text-sm">
                <code className="text-xs font-semibold text-brand-600 bg-brand-50 px-1.5 py-0.5 rounded">{"{{candidate.applied_role}}"}</code>
                <p className="text-xs text-slate-500 mt-0.5">The job they applied for</p>
              </div>
              <div className="text-sm">
                <code className="text-xs font-semibold text-brand-600 bg-brand-50 px-1.5 py-0.5 rounded">{"{{candidate.current_role}}"}</code>
                <p className="text-xs text-slate-500 mt-0.5">Their most recent job title</p>
              </div>
              <div className="text-sm">
                <code className="text-xs font-semibold text-brand-600 bg-brand-50 px-1.5 py-0.5 rounded">{"{{candidate.experience}}"}</code>
                <p className="text-xs text-slate-500 mt-0.5">Total years of experience</p>
              </div>
              <div className="text-sm">
                <code className="text-xs font-semibold text-brand-600 bg-brand-50 px-1.5 py-0.5 rounded">{"{{candidate.location}}"}</code>
                <p className="text-xs text-slate-500 mt-0.5">Candidate's city/location</p>
              </div>
            </div>
          </div>
          
        </div>
      </div>
    </div>
  );
}
