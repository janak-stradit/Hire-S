from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Any, cast

import httpx
from backend.database.session import get_session
from backend.config.settings import get_settings
from backend.models.agent_config import AgentConfig
from backend.models.user import User as UserModel
from backend.models.job import Job
from backend.api.admin.routes import require_operations_user

router = APIRouter(prefix="/agent-config", tags=["agent-config"])

class AgentConfigUpdate(BaseModel):
    agent_provider: str
    system_prompt: str
    first_speaker: str
    transcriber_model: str
    voice_provider: str
    llm_model: str
    transcriber_language: str
    transcriber_background_denoising: bool
    transcriber_confidence_threshold: float
    transcriber_keyterms: str
    transcriber_end_of_turn_confidence: float
    transcriber_min_end_of_turn_silence: int
    transcriber_max_turn_silence: int
    transcriber_smart_endpointing: bool
    transcriber_fallback_provider: str
    transcriber_fallback_language: str
    transcriber_fallback_model: str
    llm_temperature: float
    llm_max_tokens: int
    llm_emotion_recognition_enabled: bool
    llm_num_fast_turns: int
    voice_speed: float
    voice_stability: float
    voice_similarity_boost: float
    voice_optimize_streaming_latency: int
    voice_filler_injection_enabled: bool
    voice_background_sound: str
    retell_responsiveness: float
    retell_interruption_sensitivity: float
    retell_voicemail_detection: bool
    retell_ivr_hangup: bool
    retell_end_call_on_silence_ms: int
    retell_max_call_duration_ms: int
    retell_ring_duration_ms: int
    retell_boosted_keywords: str
    retell_opt_out_sensitive_data_storage: bool
    retell_fallback_voice_id: str

DEFAULT_PROMPT = """# Stradit AI Interviewer Prompt

## Identity & Purpose

You are Monika, an AI recruitment assistant for Stradit. Your primary purpose is to conduct a brief Round 1 (R1) screening call with candidates who have been shortlisted for a role. Your goal is to verify basic information, confirm their interest, and collect their availability for the next interview round.

## Voice & Persona

### Personality
- Sound friendly, welcoming, and highly professional.
- Project a polite, efficient, and encouraging demeanor.
- Maintain a warm tone to make the candidate feel comfortable and valued.
- Convey confidence in managing the preliminary screening process.

### Speech Characteristics
- Speak naturally and conversationally, using natural contractions (e.g., "I'm", "We'd").
- Speak at a measured pace.
- Ask **only one question at a time**.
- Wait patiently until the candidate finishes speaking before responding.
- Do not ask multiple questions together.
- Never invent information about the company or the role.

## Context Variables

The following information will be provided to you by the system before the call begins:
- **Candidate Name**: {{candidate.name}}
- **Applied Role**: {{candidate.applied_role}}
- **Current Role**: {{candidate.current_role}}
- **Experience**: {{candidate.experience}}
- **Location**: {{candidate.location}}

## Conversation Flow

### Introduction
Start with: "Hello {{candidate.name}}. This is Monika. I'm calling from Stradit regarding your application for the {{candidate.applied_role}} position. Do you have a couple of minutes to verify a few details?"

### Verification Questions
Proceed through these questions one by one. Do not move to the next until the candidate has answered.

1. **Name Verification**: "To start, could you please confirm your full name for our records?"
2. **Current Role & Company**: "Thank you. Could you tell me about your current role and which company you are currently working for?"
3. **Experience Verification**: "Great. Could you confirm how many years of professional experience you have in total?"
4. **Location Verification**: "And just to confirm your current location, which city are you based in right now?"
5. **Notice Period**: "Finally, what is your official notice period or how soon could you join if selected?"

### Behavioral & Soft Skills Analysis
Throughout the call, carefully analyze the candidate's communication skills, confidence, fluency, and overall behavioral traits. You must collect enough conversational data to evaluate their soft skills.

### Scheduling Process
1. **Determine Availability**: "Perfect. Since your profile has been shortlisted, we'd like to schedule you for the next interview round with our hiring team. What days and times generally work best for you next week?"
2. **Handle Specifics**: If they give a vague answer (e.g., "Anytime"), ask for a specific preference: "Would mornings or afternoons be better for you?"

### Confirmation and Wrap-up
1. **Summarize**: "I've noted that you are available on [summarize their availability]. Our team will review this and send a calendar invite to your email shortly."
2. **Close politely**: "Thank you so much for your time today, {{candidate.name}}. We look forward to speaking with you again soon. Have a great day!"

## Response Guidelines

- Keep responses concise and focused on the verification and scheduling information.
- Do not ask deeply technical interview questions. This is purely a verification call.
- Use explicit confirmation when noting down their availability.
- If a candidate does not answer clearly, politely repeat or rephrase the question.

## Scenario Handling

### If the Candidate is Not Available Right Now
1. "I completely understand. Is there a better time today or tomorrow when I could call you back?"
2. *Note their preferred callback time and gracefully end the call.* "I've noted that. We will call you back then. Have a great day!"

### If the Candidate is No Longer Interested
1. "I understand. Just to confirm, you would like to withdraw your application for the {{candidate.applied_role}} position?"
2. *If yes:* "Thank you for letting us know. We appreciate your time and wish you the best in your job search. Have a great day."

### If the Candidate Asks About Salary or Technical Details
1. "That's a great question. Because this is just a preliminary verification call, I don't have the specific details regarding compensation or the deep technical requirements in front of me."
2. "However, the hiring manager will be able to answer all of those questions during your next interview round."

## Knowledge Base

### Company Information
- **Company**: Stradit (Stradit India Private Limited)
- **Role**: You are hiring for the role they applied for ({{candidate.applied_role}}).

### Next Steps Process
- After this call, the candidate's availability is logged in the Applicant Tracking System.
- A human recruiter or hiring manager will review the availability and send an official Google Meet/Teams calendar invite to the candidate's email.
- The next round usually takes about 30 to 45 minutes and involves a technical discussion.

## Response Refinement

- When confirming complex availability: "Let me make sure I have everything correct. You are available next Tuesday after 2 PM and Thursday morning. Have I understood correctly?"
- Avoid overwhelming the candidate with long paragraphs of speech.

## Call Management

- If there are technical difficulties or you couldn't hear them: "I apologize, the line broke up for a second there. Could you please repeat that?"
- If the candidate asks you to hold: "Of course, take your time."
"""

@router.get("")
async def get_agent_config(
    _: UserModel = Depends(require_operations_user),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(AgentConfig).limit(1))
    config = result.scalars().first()
    
    if not config:
        config = AgentConfig(
            system_prompt=DEFAULT_PROMPT,
            transcriber_model="deepgram",
            voice_provider="vapi",
            llm_model="gpt-4o"
        )
        session.add(config)
        await session.commit()
        await session.refresh(config)
        
    return {
        "id": config.id,
        "agent_provider": config.agent_provider,
        "system_prompt": config.system_prompt,
        "first_speaker": config.first_speaker,
        "transcriber_model": config.transcriber_model,
        "voice_provider": config.voice_provider,
        "llm_model": config.llm_model,
        "transcriber_language": config.transcriber_language,
        "transcriber_background_denoising": config.transcriber_background_denoising,
        "transcriber_confidence_threshold": config.transcriber_confidence_threshold,
        "transcriber_keyterms": config.transcriber_keyterms,
        "transcriber_end_of_turn_confidence": config.transcriber_end_of_turn_confidence,
        "transcriber_min_end_of_turn_silence": config.transcriber_min_end_of_turn_silence,
        "transcriber_max_turn_silence": config.transcriber_max_turn_silence,
        "transcriber_smart_endpointing": config.transcriber_smart_endpointing,
        "transcriber_fallback_provider": config.transcriber_fallback_provider,
        "transcriber_fallback_language": config.transcriber_fallback_language,
        "transcriber_fallback_model": config.transcriber_fallback_model,
        "llm_temperature": config.llm_temperature,
        "llm_max_tokens": config.llm_max_tokens,
        "llm_emotion_recognition_enabled": config.llm_emotion_recognition_enabled,
        "llm_num_fast_turns": config.llm_num_fast_turns,
        "voice_speed": config.voice_speed,
        "voice_stability": config.voice_stability,
        "voice_similarity_boost": config.voice_similarity_boost,
        "voice_optimize_streaming_latency": config.voice_optimize_streaming_latency,
        "voice_filler_injection_enabled": config.voice_filler_injection_enabled,
        "voice_background_sound": config.voice_background_sound,
        "retell_responsiveness": config.retell_responsiveness,
        "retell_interruption_sensitivity": config.retell_interruption_sensitivity,
        "retell_voicemail_detection": config.retell_voicemail_detection,
        "retell_ivr_hangup": config.retell_ivr_hangup,
        "retell_end_call_on_silence_ms": config.retell_end_call_on_silence_ms,
        "retell_max_call_duration_ms": config.retell_max_call_duration_ms,
        "retell_ring_duration_ms": config.retell_ring_duration_ms,
        "retell_boosted_keywords": config.retell_boosted_keywords,
        "retell_opt_out_sensitive_data_storage": config.retell_opt_out_sensitive_data_storage,
        "retell_fallback_voice_id": config.retell_fallback_voice_id
    }

@router.put("")
async def update_agent_config(
    data: AgentConfigUpdate,
    _: UserModel = Depends(require_operations_user),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(AgentConfig).limit(1))
    config = result.scalars().first()
    
    if not config:
        config = AgentConfig(system_prompt=DEFAULT_PROMPT)
        session.add(config)
        
    cast(Any, config).agent_provider = data.agent_provider
    cast(Any, config).system_prompt = data.system_prompt
    cast(Any, config).first_speaker = data.first_speaker
    cast(Any, config).transcriber_model = data.transcriber_model
    cast(Any, config).voice_provider = data.voice_provider
    cast(Any, config).llm_model = data.llm_model
    cast(Any, config).transcriber_language = data.transcriber_language
    cast(Any, config).transcriber_background_denoising = data.transcriber_background_denoising
    cast(Any, config).transcriber_confidence_threshold = data.transcriber_confidence_threshold
    cast(Any, config).transcriber_keyterms = data.transcriber_keyterms
    cast(Any, config).transcriber_end_of_turn_confidence = data.transcriber_end_of_turn_confidence
    cast(Any, config).transcriber_min_end_of_turn_silence = data.transcriber_min_end_of_turn_silence
    cast(Any, config).transcriber_max_turn_silence = data.transcriber_max_turn_silence
    cast(Any, config).transcriber_smart_endpointing = data.transcriber_smart_endpointing
    cast(Any, config).transcriber_fallback_provider = data.transcriber_fallback_provider
    cast(Any, config).transcriber_fallback_language = data.transcriber_fallback_language
    cast(Any, config).transcriber_fallback_model = data.transcriber_fallback_model
    cast(Any, config).llm_temperature = data.llm_temperature
    cast(Any, config).llm_max_tokens = data.llm_max_tokens
    cast(Any, config).llm_emotion_recognition_enabled = data.llm_emotion_recognition_enabled
    cast(Any, config).llm_num_fast_turns = data.llm_num_fast_turns
    cast(Any, config).voice_speed = data.voice_speed
    cast(Any, config).voice_stability = data.voice_stability
    cast(Any, config).voice_similarity_boost = data.voice_similarity_boost
    cast(Any, config).voice_optimize_streaming_latency = data.voice_optimize_streaming_latency
    cast(Any, config).voice_filler_injection_enabled = data.voice_filler_injection_enabled
    cast(Any, config).voice_background_sound = data.voice_background_sound
    cast(Any, config).retell_responsiveness = data.retell_responsiveness
    cast(Any, config).retell_interruption_sensitivity = data.retell_interruption_sensitivity
    cast(Any, config).retell_voicemail_detection = data.retell_voicemail_detection
    cast(Any, config).retell_ivr_hangup = data.retell_ivr_hangup
    cast(Any, config).retell_end_call_on_silence_ms = data.retell_end_call_on_silence_ms
    cast(Any, config).retell_max_call_duration_ms = data.retell_max_call_duration_ms
    cast(Any, config).retell_ring_duration_ms = data.retell_ring_duration_ms
    cast(Any, config).retell_boosted_keywords = data.retell_boosted_keywords
    cast(Any, config).retell_opt_out_sensitive_data_storage = data.retell_opt_out_sensitive_data_storage
    cast(Any, config).retell_fallback_voice_id = data.retell_fallback_voice_id
    
    # If using Retell, create the LLM and Agent in Retell
    if config.agent_provider == "retell":
        settings = get_settings()
        if settings.retell_api_key:
            async with httpx.AsyncClient() as client:
                # 1. Update or Create Retell LLM
                prompt_text = data.system_prompt
                if data.first_speaker == "user":
                    prompt_text += "\n\nIMPORTANT: Wait for the user to speak first before saying anything. Do not say anything until the user has spoken."

                valid_retell_models = {
                    "gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", 
                    "gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-5.1", "gpt-5.2", "gpt-5.4", 
                    "gpt-5.4-mini", "gpt-5.4-nano", "gpt-5.5", "gpt-5.6-terra", "gpt-5.6-luna", 
                    "claude-4.0-sonnet", "claude-4.5-sonnet", "claude-4.6-sonnet", "claude-5-sonnet", 
                    "claude-4.5-haiku", "gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-2.5-flash", 
                    "gemini-2.5-flash-lite", "gemini-3.0-flash", "gemini-3.1-flash-lite", "gemini-3.5-flash"
                }
                model_to_use = data.llm_model if data.llm_model in valid_retell_models else "gpt-4o"

                llm_payload: dict[str, Any] = {
                    "general_prompt": prompt_text,
                    "model": model_to_use
                }
                
                if config.retell_llm_id:
                    llm_resp = await client.patch(
                        f"https://api.retellai.com/update-retell-llm/{config.retell_llm_id}",
                        headers={"Authorization": f"Bearer {settings.retell_api_key}"},
                        json=llm_payload
                    )
                    if llm_resp.status_code >= 400:
                        print("RETELL LLM UPDATE ERROR:", llm_resp.text)
                        raise HTTPException(status_code=400, detail=f"Retell LLM update error: {llm_resp.text}")
                else:
                    llm_payload["general_tools"] = []
                    llm_resp = await client.post(
                        "https://api.retellai.com/create-retell-llm",
                        headers={"Authorization": f"Bearer {settings.retell_api_key}"},
                        json=llm_payload
                    )
                    if llm_resp.status_code >= 400:
                        print("RETELL LLM CREATE ERROR:", llm_resp.text)
                        raise HTTPException(status_code=400, detail=f"Retell LLM creation error: {llm_resp.text}")
                    if llm_resp.status_code == 201:
                        llm_data = llm_resp.json()
                        cast(Any, config).retell_llm_id = llm_data.get("llm_id")
                
                # Map transcriber language to valid Retell format
                lang_map = {"en": "en-US", "es": "es-ES", "fr": "fr-FR", "auto": "multi"}
                mapped_lang = lang_map.get(data.transcriber_language, data.transcriber_language)

                # 2. Update or Create Retell Agent
                agent_payload: dict[str, Any] = {
                    "voice_id": data.voice_provider if data.voice_provider.startswith(("11labs-", "deepgram-", "openai-", "azure-", "cartesia-")) else ("11labs-Adrian" if data.voice_provider == "11labs" else "openai-Monika"),
                    "agent_name": "HireX Interviewer",
                    "language": mapped_lang,
                    "responsiveness": data.retell_responsiveness,
                    "interruption_sensitivity": data.retell_interruption_sensitivity,
                    "ambient_sound": data.voice_background_sound if data.voice_background_sound in ["coffee-shop", "office", "summer-outdoor", "mountain-wind"] else None,
                    "end_call_after_silence_ms": data.retell_end_call_on_silence_ms,
                    "max_call_duration_ms": data.retell_max_call_duration_ms,
                    "post_call_analysis_data": [
                        {"name": "years_of_experience", "type": "string", "description": "The candidate's total years of experience."},
                        {"name": "location", "type": "string", "description": "The candidate's current or preferred location."},
                        {"name": "notice_period", "type": "string", "description": "The candidate's notice period in days or months."},
                        {"name": "current_company", "type": "string", "description": "The current company the candidate is working for."},
                        {"name": "current_role", "type": "string", "description": "The current role or title of the candidate."},
                        {"name": "communication_skills", "type": "string", "description": "Analysis of the candidate's communication skills and fluency."},
                        {"name": "behavioral_analysis", "type": "string", "description": "Detailed analysis of the candidate's behavior during the interview."}
                    ],
                    "opt_out_sensitive_data_storage": data.retell_opt_out_sensitive_data_storage
                }
                
                if data.retell_fallback_voice_id:
                    agent_payload["fallback_voice_ids"] = [data.retell_fallback_voice_id]
                
                # Optionals that depend on conditionals
                if data.retell_voicemail_detection:
                    agent_payload["voicemail_message"] = "Hello, I am calling from Stradit regarding your job application. We will try reaching out again later."
                    agent_payload["voicemail_detection"] = "detect_voicemail_and_leave_message"
                    
                if data.retell_ring_duration_ms > 0:
                    agent_payload["ring_duration_ms"] = data.retell_ring_duration_ms

                boosted_keywords_list = [k.strip() for k in data.retell_boosted_keywords.split(",") if k.strip()]
                if boosted_keywords_list:
                    agent_payload["boosted_keywords"] = boosted_keywords_list
                
                if config.retell_llm_id:
                    agent_payload["response_engine"] = {
                        "type": "retell-llm",
                        "llm_id": config.retell_llm_id
                    }
                    
                    if config.retell_agent_id:
                        agent_resp = await client.patch(
                            f"https://api.retellai.com/update-agent/{config.retell_agent_id}",
                            headers={"Authorization": f"Bearer {settings.retell_api_key}"},
                            json=agent_payload
                        )
                        if agent_resp.status_code >= 400:
                            print("RETELL AGENT UPDATE ERROR:", agent_resp.text)
                            raise HTTPException(status_code=400, detail=f"Retell Agent update error: {agent_resp.text}")
                    else:
                        agent_resp = await client.post(
                            "https://api.retellai.com/create-agent",
                            headers={"Authorization": f"Bearer {settings.retell_api_key}"},
                            json=agent_payload
                        )
                        if agent_resp.status_code >= 400:
                            print("RETELL AGENT CREATE ERROR:", agent_resp.text)
                            raise HTTPException(status_code=400, detail=f"Retell Agent creation error: {agent_resp.text}")
                        if agent_resp.status_code == 201:
                            cast(Any, config).retell_agent_id = agent_resp.json().get("agent_id")
                            
    await session.commit()
    return {"message": "Agent configuration updated"}

class JobPromptUpdate(BaseModel):
    agent_prompt: str

@router.get("/jobs")
async def get_agent_jobs(
    _: UserModel = Depends(require_operations_user),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(Job.job_id, Job.title, Job.vapi_prompt).order_by(Job.title))
    jobs = result.all()
    return [{"id": j.job_id, "title": j.title, "agent_prompt": j.vapi_prompt} for j in jobs]

@router.put("/jobs/{job_id}/prompt")
async def update_job_agent_prompt(
    job_id: str,
    data: JobPromptUpdate,
    _: UserModel = Depends(require_operations_user),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(Job).filter(Job.job_id == job_id))
    job = result.scalars().first()
    if not job:
        return {"error": "Job not found"}
    
    cast(Any, job).vapi_prompt = data.agent_prompt
    await session.commit()
    return {"message": "Job prompt updated"}
