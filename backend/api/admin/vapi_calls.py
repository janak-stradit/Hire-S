import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database.session import get_session
from backend.models.application import Application
from backend.models.candidate import CandidateProfile
from backend.models.job import Job
from backend.models.user import User as UserModel
from backend.models.vapi_config import VapiConfig
from backend.models.vapi_call import VapiCall
from backend.api.admin.routes import require_operations_user
from backend.config.settings import get_settings

router = APIRouter(prefix="/candidates/{app_id}", tags=["vapi-calls"])
settings = get_settings()

@router.post("/vapi-schedule")
async def schedule_vapi_interview(
    app_id: str,
    _: UserModel = Depends(require_operations_user),
    session: AsyncSession = Depends(get_session)
):
    if not settings.vapi_api_key:
        raise HTTPException(status_code=500, detail="VAPI_API_KEY is not configured")

    # Fetch Application, Candidate, and Job
    result = await session.execute(
        select(Application, CandidateProfile, Job)
        .join(CandidateProfile, Application.candidate_id == CandidateProfile.candidate_id)
        .join(Job, Application.job_id == Job.job_id)
        .filter(Application.application_id == app_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
    
    app, candidate, job = row

    # Fetch VapiConfig
    config_res = await session.execute(select(VapiConfig).limit(1))
    config = config_res.scalars().first()
    if not config:
        raise HTTPException(status_code=500, detail="Vapi configuration not found")

    # Determine prompt (job specific override or global)
    prompt = job.vapi_prompt if job.vapi_prompt else config.system_prompt

    # Safely format variables
    name = f"{candidate.first_name or ''} {candidate.last_name or ''}".strip() or "Candidate"
    experience = f"{candidate.total_experience} years" if candidate.total_experience is not None else "Not specified"
    location = candidate.city if candidate.city else "Not specified"

    # Handlebars replacement
    prompt = prompt.replace("{{candidate.name}}", name)
    prompt = prompt.replace("{{candidate.applied_role}}", job.title)
    prompt = prompt.replace("{{candidate.current_role}}", candidate.current_role or "Not specified")
    prompt = prompt.replace("{{candidate.experience}}", experience)
    prompt = prompt.replace("{{candidate.location}}", location)

    # Build Vapi Payload for Web Call
    # https://docs.vapi.ai/api-reference/calls/create-web-call
    
    # Determine the model mapping based on the UI dropdown values
    config_model = (config.llm_model or "").lower()
    
    if config_model == "anthropic-bedrock" or config_model == "anthropic":
        llm_provider = "anthropic"
        llm_model_str = "claude-3-haiku-20240307"
    elif config_model == "gpt-4o":
        llm_provider = "openai"
        llm_model_str = "gpt-4o"
    else:
        # Fallback to a safe default if somehow invalid
        llm_provider = "openai"
        llm_model_str = "gpt-4o-mini"
    
    payload = {
        "assistant": {
            "firstMessage": f"Hello {candidate.first_name}, I am your AI recruiter. Can you hear me clearly?",
            "firstMessageMode": "assistant-speaks-first",
            "model": {
                "provider": llm_provider,
                "model": llm_model_str,
                "messages": [
                    {
                        "role": "system",
                        "content": prompt
                    }
                ]
            },
            "voice": {
                "provider": "11labs",
                "voiceId": "bIHbv24MWmeRgasZH58o"
            },
            "transcriber": {
                "provider": config.transcriber_model,
                "language": config.transcriber_language
            },
            "recordingEnabled": True
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.vapi.ai/call/web",
            headers={"Authorization": f"Bearer {settings.vapi_api_key}"},
            json=payload,
            timeout=10.0
        )
        
        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Vapi API Error: {response.text}")
            
        vapi_data = response.json()
        call_id = vapi_data.get("id")
        web_call_url = vapi_data.get("webCallUrl")
        
        if not call_id:
            raise HTTPException(status_code=502, detail="Vapi did not return a call ID")

    # Save to database
    vapi_call = VapiCall(
        application_id=app_id,
        vapi_call_id=call_id,
        web_call_url=web_call_url,
        status="queued"
    )
    session.add(vapi_call)
    await session.commit()
    
    return {"message": "Web call scheduled successfully", "vapi_call_id": call_id, "web_call_url": web_call_url}


@router.get("/vapi-status")
async def check_vapi_status(
    app_id: str,
    _: UserModel = Depends(require_operations_user),
    session: AsyncSession = Depends(get_session)
):
    if not settings.vapi_api_key:
        raise HTTPException(status_code=500, detail="VAPI_API_KEY is not configured")

    result = await session.execute(
        select(VapiCall).filter(VapiCall.application_id == app_id).order_by(VapiCall.created_at.desc())
    )
    vapi_call = result.scalars().first()
    
    if not vapi_call:
        return {"status": "none"}
        
    # If it's already ended, just return the data we have
    if vapi_call.status == "ended":
        return {
            "status": "ended",
            "transcript": vapi_call.transcript,
            "summary": vapi_call.summary,
            "recording_url": vapi_call.recording_url,
            "web_call_url": vapi_call.web_call_url
        }
        
    # Otherwise, poll Vapi
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.vapi.ai/call/{vapi_call.vapi_call_id}",
            headers={"Authorization": f"Bearer {settings.vapi_api_key}"},
            timeout=10.0
        )
        
        if response.status_code == 200:
            vapi_data = response.json()
            new_status = vapi_data.get("status")
            
            if new_status and new_status != vapi_call.status:
                vapi_call.status = new_status
                if new_status == "ended":
                    vapi_call.transcript = vapi_data.get("transcript")
                    vapi_call.summary = vapi_data.get("summary")
                    vapi_call.recording_url = vapi_data.get("recordingUrl")
                await session.commit()
                
            return {
                "status": vapi_call.status,
                "transcript": vapi_call.transcript,
                "summary": vapi_call.summary,
                "recording_url": vapi_call.recording_url,
                "web_call_url": vapi_call.web_call_url
            }
            
        return {"status": vapi_call.status, "web_call_url": vapi_call.web_call_url}
