from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from backend.database.session import get_session
from backend.models.vapi_config import VapiConfig
from backend.models.user import User as UserModel
from backend.models.job import Job
from backend.api.admin.routes import require_operations_user

router = APIRouter(prefix="/vapi-config", tags=["vapi-config"])

class VapiConfigUpdate(BaseModel):
    system_prompt: str
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

DEFAULT_PROMPT = """# Stradit AI Interviewer Prompt

## Identity & Purpose

You are Naina, an AI recruitment assistant for Stradit. Your primary purpose is to conduct a brief Round 1 (R1) screening call with candidates who have been shortlisted for a role. Your goal is to verify basic information, confirm their interest, and collect their availability for the next interview round.

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
Start with: "Hello {{candidate.name}}. This is Naina. I'm calling from Stradit regarding your application for the {{candidate.applied_role}} position. Do you have a couple of minutes to verify a few details?"

### Verification Questions
Proceed through these questions one by one. Do not move to the next until the candidate has answered.

1. **Name Verification**: "To start, could you please confirm your full name for our records?"
2. **Experience Verification**: "Great. I see you have some solid experience. Could you confirm how many years of professional experience you have in total?"
3. **Location Verification**: "Thank you. And just to confirm your current location, which city are you based in right now?"

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
async def get_vapi_config(
    _: UserModel = Depends(require_operations_user),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(VapiConfig).limit(1))
    config = result.scalars().first()
    
    if not config:
        config = VapiConfig(
            system_prompt=DEFAULT_PROMPT,
            transcriber_model="assemblyai",
            voice_provider="vapi",
            llm_model="anthropic-bedrock"
        )
        session.add(config)
        await session.commit()
        await session.refresh(config)
        
    return {
        "id": config.id,
        "system_prompt": config.system_prompt,
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
        "voice_background_sound": config.voice_background_sound
    }

@router.put("")
async def update_vapi_config(
    data: VapiConfigUpdate,
    _: UserModel = Depends(require_operations_user),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(VapiConfig).limit(1))
    config = result.scalars().first()
    
    if not config:
        config = VapiConfig(system_prompt=DEFAULT_PROMPT)
        session.add(config)
        
    config.system_prompt = data.system_prompt
    config.transcriber_model = data.transcriber_model
    config.voice_provider = data.voice_provider
    config.llm_model = data.llm_model
    config.transcriber_language = data.transcriber_language
    config.transcriber_background_denoising = data.transcriber_background_denoising
    config.transcriber_confidence_threshold = data.transcriber_confidence_threshold
    config.transcriber_keyterms = data.transcriber_keyterms
    config.transcriber_end_of_turn_confidence = data.transcriber_end_of_turn_confidence
    config.transcriber_min_end_of_turn_silence = data.transcriber_min_end_of_turn_silence
    config.transcriber_max_turn_silence = data.transcriber_max_turn_silence
    config.transcriber_smart_endpointing = data.transcriber_smart_endpointing
    config.transcriber_fallback_provider = data.transcriber_fallback_provider
    config.transcriber_fallback_language = data.transcriber_fallback_language
    config.transcriber_fallback_model = data.transcriber_fallback_model
    config.llm_temperature = data.llm_temperature
    config.llm_max_tokens = data.llm_max_tokens
    config.llm_emotion_recognition_enabled = data.llm_emotion_recognition_enabled
    config.llm_num_fast_turns = data.llm_num_fast_turns
    config.voice_speed = data.voice_speed
    config.voice_stability = data.voice_stability
    config.voice_similarity_boost = data.voice_similarity_boost
    config.voice_optimize_streaming_latency = data.voice_optimize_streaming_latency
    config.voice_filler_injection_enabled = data.voice_filler_injection_enabled
    config.voice_background_sound = data.voice_background_sound
    
    await session.commit()
    return {"message": "Vapi configuration updated"}

class JobPromptUpdate(BaseModel):
    vapi_prompt: str

@router.get("/jobs")
async def get_vapi_jobs(
    _: UserModel = Depends(require_operations_user),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(Job.job_id, Job.title, Job.vapi_prompt).order_by(Job.title))
    jobs = result.all()
    return [{"id": j.job_id, "title": j.title, "vapi_prompt": j.vapi_prompt} for j in jobs]

@router.put("/jobs/{job_id}/prompt")
async def update_job_vapi_prompt(
    job_id: str,
    data: JobPromptUpdate,
    _: UserModel = Depends(require_operations_user),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(Job).filter(Job.job_id == job_id))
    job = result.scalars().first()
    if not job:
        return {"error": "Job not found"}
    
    job.vapi_prompt = data.vapi_prompt
    await session.commit()
    return {"message": "Job prompt updated"}
