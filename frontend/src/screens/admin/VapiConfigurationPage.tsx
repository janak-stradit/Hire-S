"use client";

import { useEffect, useState } from "react";
import { ArrowLeft, Save, Loader2, Bot, Mic, Zap, CheckCircle2, Settings2, AudioLines } from "lucide-react";
import { apiClient } from "../../api/client";
import { useRouter } from "next/navigation";

export default function VapiConfigurationPage() {
  const router = useRouter();
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  
  const COST_RATES = {
    transcriber: {
      assemblyai: { cost: 0.003, latency: 90, name: "Assembly AI (English)" },
      deepgram: { cost: 0.004, latency: 150, name: "Deepgram" },
      talkscriber: { cost: 0.005, latency: 200, name: "Talkscriber" }
    },
    llm: {
      "anthropic-bedrock": { cost: 0.00, latency: 0, name: "Anthropic Bedrock (Claude Sonnet 4)" },
      "gpt-4o": { cost: 0.04, latency: 400, name: "OpenAI (GPT-4o)" },
      "anthropic": { cost: 0.03, latency: 350, name: "Anthropic (Claude 3)" },
    },
    voice: {
      "vapi": { cost: 0.02, latency: 250, name: "Vapi (Naina)" },
      "11labs": { cost: 0.06, latency: 300, name: "11Labs" },
      "cartesia": { cost: 0.03, latency: 200, name: "Cartesia" },
    }
  };
  
  const [globalSystemPrompt, setGlobalSystemPrompt] = useState("");
  
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
  const [jobs, setJobs] = useState<{id: string, title: string, vapi_prompt: string | null}[]>([]);
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
      apiClient.get("/admin/vapi-config"),
      apiClient.get("/admin/vapi-config/jobs")
    ])
      .then(([configRes, jobsRes]) => {
        const config = configRes.data;
        setGlobalSystemPrompt(config.system_prompt || "");
        
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
          if (j.vapi_prompt) initialJobPrompts[j.id] = j.vapi_prompt;
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
      await apiClient.put("/admin/vapi-config", {
        system_prompt: globalSystemPrompt,
        
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
        await apiClient.put(`/admin/vapi-config/jobs/${selectedJobId}/prompt`, {
          vapi_prompt: jobPrompts[selectedJobId] || ""
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
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Advanced Transcriber Settings */}
          <div className="card card-body space-y-5 h-full">
            <h2 className="section-label flex items-center gap-2 border-b border-slate-100 pb-3">
              <Mic className="h-4 w-4 text-brand-500" /> Transcriber Settings
            </h2>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-slate-700">Provider</label>
                  <select value={transcriber} onChange={e => setTranscriber(e.target.value)} className="input text-sm">
                    <option value="assemblyai">Assembly AI (English)</option>
                    <option value="deepgram">Deepgram</option>
                    <option value="talkscriber">Talkscriber</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-slate-700">Language</label>
                  <select value={transcriberLanguage} onChange={e => setTranscriberLanguage(e.target.value)} className="input text-sm">
                    <option value="auto">Auto-detect</option>
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                    <option value="multi">Multilingual</option>
                  </select>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700 flex justify-between">
                  <span>Confidence Threshold</span>
                  <span className="text-slate-500">{transcriberConfidenceThreshold.toFixed(2)}</span>
                </label>
                <input type="range" min="0" max="1" step="0.05" value={transcriberConfidenceThreshold} onChange={e => setTranscriberConfidenceThreshold(parseFloat(e.target.value))} className="w-full accent-brand-600" />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700 flex justify-between">
                  <span>EOT Confidence</span>
                  <span className="text-slate-500">{transcriberEndOfTurnConfidence.toFixed(2)}</span>
                </label>
                <input type="range" min="0" max="1" step="0.05" value={transcriberEndOfTurnConfidence} onChange={e => setTranscriberEndOfTurnConfidence(parseFloat(e.target.value))} className="w-full accent-brand-600" />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-700">Min EOT Silence (ms)</label>
                  <input type="number" value={transcriberMinEndOfTurnSilence} onChange={e => setTranscriberMinEndOfTurnSilence(parseInt(e.target.value) || 0)} className="input text-sm" />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-700">Max Turn Silence (ms)</label>
                  <input type="number" value={transcriberMaxTurnSilence} onChange={e => setTranscriberMaxTurnSilence(parseInt(e.target.value) || 0)} className="input text-sm" />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700">Keyterms Prompt</label>
                <input type="text" value={transcriberKeyterms} onChange={e => setTranscriberKeyterms(e.target.value)} placeholder="e.g. Vapi, API, webhook" className="input text-sm" />
              </div>

              <div className="flex flex-col gap-2">
                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input type="checkbox" checked={transcriberBackgroundDenoising} onChange={e => setTranscriberBackgroundDenoising(e.target.checked)} className="rounded text-brand-600 focus:ring-brand-500 h-4 w-4" />
                  Enable Background Denoising
                </label>
                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input type="checkbox" checked={transcriberSmartEndpointing} onChange={e => setTranscriberSmartEndpointing(e.target.checked)} className="rounded text-brand-600 focus:ring-brand-500 h-4 w-4" />
                  Enable Smart Endpointing
                </label>
              </div>

              <div className="pt-4 border-t border-slate-100">
                <h3 className="text-xs font-semibold text-slate-500 mb-3 uppercase tracking-wider">Fallback Settings</h3>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <label className="text-xs font-medium text-slate-600">Provider</label>
                    <select value={transcriberFallbackProvider} onChange={e => setTranscriberFallbackProvider(e.target.value)} className="input text-sm py-1.5">
                      <option value="deepgram">Deepgram</option>
                      <option value="talkscriber">Talkscriber</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs font-medium text-slate-600">Model</label>
                    <input type="text" value={transcriberFallbackModel} onChange={e => setTranscriberFallbackModel(e.target.value)} className="input text-sm py-1.5" />
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Advanced Language Model Settings */}
          <div className="card card-body space-y-5 h-full">
            <h2 className="section-label flex items-center gap-2 border-b border-slate-100 pb-3">
              <Zap className="h-4 w-4 text-brand-500" /> Language Model (LLM)
            </h2>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700">Model</label>
                <select value={llmModel} onChange={e => setLlmModel(e.target.value)} className="input text-sm">
                  <option value="anthropic-bedrock">Anthropic Bedrock (Claude Sonnet 4)</option>
                  <option value="gpt-4o">OpenAI (GPT-4o)</option>
                  <option value="azure-openai">Azure OpenAI</option>
                  <option value="anthropic">Anthropic (Claude 3)</option>
                  <option value="minimax">MiniMax</option>
                  <option value="google">Google</option>
                  <option value="groq">Groq</option>
                  <option value="openrouter">OpenRouter (Llama 3)</option>
                  <option value="custom">Custom LLM</option>
                  <option value="cerebras">Cerebras</option>
                  <option value="deepseek">Deep seek</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700 flex justify-between">
                  <span>Temperature</span>
                  <span className="text-slate-500">{llmTemperature.toFixed(2)}</span>
                </label>
                <input type="range" min="0" max="2" step="0.05" value={llmTemperature} onChange={e => setLlmTemperature(parseFloat(e.target.value))} className="w-full accent-brand-600" />
                <p className="text-[10px] text-slate-500">Lower is more deterministic, higher is more creative.</p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-700">Max Tokens</label>
                  <input type="number" value={llmMaxTokens} onChange={e => setLlmMaxTokens(parseInt(e.target.value) || 0)} className="input text-sm" />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-700">Fast Turns (Count)</label>
                  <input type="number" value={llmNumFastTurns} onChange={e => setLlmNumFastTurns(parseInt(e.target.value) || 0)} className="input text-sm" />
                </div>
              </div>

              <div className="pt-2">
                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input type="checkbox" checked={llmEmotionRecognitionEnabled} onChange={e => setLlmEmotionRecognitionEnabled(e.target.checked)} className="rounded text-brand-600 focus:ring-brand-500 h-4 w-4" />
                  Enable Emotion Recognition
                </label>
                <p className="text-xs text-slate-500 mt-1 pl-6">Analyses the user's emotion to provide empathetic responses.</p>
              </div>
            </div>
            
            <div className="rounded-xl bg-blue-50 p-4 border border-blue-100 mt-auto">
              <p className="text-xs text-blue-800 leading-relaxed">
                <strong>Tip:</strong> For phone interviews, Anthropic Bedrock offers the best logic/latency tradeoff.
              </p>
            </div>
          </div>

          {/* Advanced Voice Settings */}
          <div className="card card-body space-y-5 h-full">
            <h2 className="section-label flex items-center gap-2 border-b border-slate-100 pb-3">
              <AudioLines className="h-4 w-4 text-brand-500" /> Voice Settings
            </h2>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700">Voice Provider</label>
                <select value={voiceProvider} onChange={e => setVoiceProvider(e.target.value)} className="input text-sm">
                  <option value="vapi">Vapi (Naina)</option>
                  <option value="cartesia">Cartesia</option>
                  <option value="xai">xAI</option>
                  <option value="deepgram">Deepgram Aura</option>
                  <option value="openai">OpenAI TTS</option>
                  <option value="11labs">11Labs</option>
                  <option value="inworld">Inworld</option>
                  <option value="minimax">MiniMax</option>
                  <option value="azure">Azure Voice</option>
                  <option value="rimeai">Rime AI</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700 flex justify-between">
                  <span>Speed</span>
                  <span className="text-slate-500">{voiceSpeed.toFixed(2)}x</span>
                </label>
                <input type="range" min="0.5" max="2" step="0.05" value={voiceSpeed} onChange={e => setVoiceSpeed(parseFloat(e.target.value))} className="w-full accent-brand-600" />
              </div>

              {voiceProvider === '11labs' && (
                <>
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700 flex justify-between">
                      <span>Stability</span>
                      <span className="text-slate-500">{voiceStability.toFixed(2)}</span>
                    </label>
                    <input type="range" min="0" max="1" step="0.05" value={voiceStability} onChange={e => setVoiceStability(parseFloat(e.target.value))} className="w-full accent-brand-600" />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700 flex justify-between">
                      <span>Similarity Boost</span>
                      <span className="text-slate-500">{voiceSimilarityBoost.toFixed(2)}</span>
                    </label>
                    <input type="range" min="0" max="1" step="0.05" value={voiceSimilarityBoost} onChange={e => setVoiceSimilarityBoost(parseFloat(e.target.value))} className="w-full accent-brand-600" />
                  </div>
                </>
              )}

              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700">Streaming Latency Optimization</label>
                <select value={voiceOptimizeStreamingLatency} onChange={e => setVoiceOptimizeStreamingLatency(parseInt(e.target.value))} className="input text-sm">
                  <option value={0}>0 - Default</option>
                  <option value={1}>1 - Normal</option>
                  <option value={2}>2 - Strong</option>
                  <option value={3}>3 - Max</option>
                  <option value={4}>4 - Extreme</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-2">
                <div className="flex flex-col gap-2">
                  <label className="flex items-center gap-2 text-sm text-slate-700">
                    <input type="checkbox" checked={voiceFillerInjectionEnabled} onChange={e => setVoiceFillerInjectionEnabled(e.target.checked)} className="rounded text-brand-600 focus:ring-brand-500 h-4 w-4" />
                    Filler Injection
                  </label>
                  <p className="text-[10px] text-slate-500 pl-6">Adds "Umm", "Ah" while thinking.</p>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-700">Background Sound</label>
                  <select value={voiceBackgroundSound} onChange={e => setVoiceBackgroundSound(e.target.value)} className="input text-sm py-1">
                    <option value="off">Off</option>
                    <option value="office">Office</option>
                    <option value="cafe">Cafe</option>
                  </select>
                </div>
              </div>

            </div>
          </div>
          
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
