import httpx
import typing
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.database.session import get_session
from backend.models.application import Application
from backend.models.candidate import CandidateProfile
from backend.models.job import Job
from backend.models.user import User as UserModel
from backend.models.agent_config import AgentConfig
from backend.models.agent_call import AgentCall
from backend.models.retell_call import RetellCall
from backend.api.admin.routes import require_operations_user
from backend.config.settings import get_settings

router = APIRouter(prefix="/candidates/{app_id}", tags=["agent-calls"])
settings = get_settings()

@router.post("/agent-schedule")
async def schedule_agent_interview(
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

    # Fetch AgentConfig
    config_res = await session.execute(select(AgentConfig).limit(1))
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
    
    # Build voice payload based on config
    voice_provider = (config.voice_provider or "vapi").lower()
    voice_payload = {}
    if voice_provider == "11labs":
        voice_payload = {
            "provider": "11labs",
            "voiceId": "pNInz6obpgDQGcFmaJgB" # standard ElevenLabs voice
        }
    elif voice_provider == "cartesia":
        voice_payload = {
            "provider": "cartesia",
            "voiceId": "248be419-c632-4f23-adf1-5324ed7dbf1d"
        }
    else:
        # Default Vapi/PlayHT or other provider
        voice_payload = {
            "provider": "playht",
            "voiceId": "jennifer"
        }

    payload = {
        "assistant": {
            "firstMessage": f"Hello {candidate.first_name}, I am your AI recruiter. Can you hear me clearly?",
            "firstMessageMode": "assistant-speaks-first" if config.first_speaker == "ai" else "assistant-waits-for-user",
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
            "voice": voice_payload,
            "transcriber": {
                "provider": config.transcriber_model,
                "language": config.transcriber_language
            },
            "recordingEnabled": True
        }
    }
    import httpx
    
    async with httpx.AsyncClient() as client:
        if config.agent_provider == "retell":
            if not settings.retell_api_key or not config.retell_agent_id:
                raise HTTPException(status_code=500, detail="Retell configuration missing (API Key or Agent ID)")
            
            # Retell dynamic variables (keys must match the {{...}} in the prompt)
            dynamic_vars = {
                "candidate.name": name,
                "candidate.applied_role": job.title,
                "candidate.current_role": candidate.current_role or "Not specified",
                "candidate.experience": experience,
                "candidate.location": location
            }
            
            response = await client.post(
                "https://api.retellai.com/v2/create-web-call",
                headers={
                    "Authorization": f"Bearer {settings.retell_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "agent_id": config.retell_agent_id,
                    "retell_llm_dynamic_variables": dynamic_vars
                },
                timeout=10.0
            )
            
            if response.status_code >= 400:
                raise HTTPException(status_code=502, detail=f"Retell API Error: {response.text}")
                
            retell_data = response.json()
            call_id = retell_data.get("call_id")
            access_token = retell_data.get("access_token")
            
            if not call_id or not access_token:
                raise HTTPException(status_code=502, detail="Retell did not return a call ID or access token")
                
            # Construct local web call URL
            web_call_url = f"http://localhost:3001/retell-call/{access_token}"
            
        else:
            # Default Vapi flow
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
    call_record: AgentCall | RetellCall
    if config and config.agent_provider == "retell":
        call_record = RetellCall(
            application_id=app_id,
            retell_call_id=call_id,
            web_call_url=web_call_url,
            status="queued"
        )
    else:
        call_record = AgentCall(
            application_id=app_id,
            vapi_call_id=call_id,
            web_call_url=web_call_url,
            status="queued"
        )
        
    session.add(call_record)
    await session.commit()
    
    return {"message": "Web call scheduled successfully", "agent_call_id": call_id, "web_call_url": web_call_url}


@router.get("/agent-status")
async def check_agent_status(
    app_id: str,
    _: UserModel = Depends(require_operations_user),
    session: AsyncSession = Depends(get_session)
):
    if not settings.vapi_api_key:
        raise HTTPException(status_code=500, detail="VAPI_API_KEY is not configured")

    # Fetch from both tables to find the latest call
    vapi_res = await session.execute(
        select(AgentCall).filter(AgentCall.application_id == app_id).order_by(AgentCall.created_at.desc())
    )
    agent_call = vapi_res.scalars().first()
    
    retell_res = await session.execute(
        select(RetellCall).filter(RetellCall.application_id == app_id).order_by(RetellCall.created_at.desc())
    )
    retell_call = retell_res.scalars().first()
    
    if not agent_call and not retell_call:
        return {"status": "none"}
        
    # Pick the most recent one
    from typing import cast
    call_record: AgentCall | RetellCall | None = None
    is_retell = False
    
    if agent_call and retell_call:
        if retell_call.created_at > agent_call.created_at:
            call_record = retell_call
            is_retell = True
        else:
            call_record = agent_call
    elif retell_call:
        call_record = retell_call
        is_retell = True
    else:
        call_record = agent_call
        
    # Check if we should keep polling because Retell hasn't finished analysis yet
    is_missing_retell_analysis = is_retell and call_record and call_record.status == "ended" and call_record.summary in [None, "No summary available"]

    # If it's already ended and we have a valid summary, return data
    if call_record and call_record.status == "ended" and not is_missing_retell_analysis:
        result: dict[str, typing.Any] = {
            "status": "ended",
            "transcript": call_record.transcript,
            "summary": call_record.summary,
            "recording_url": call_record.recording_url,
            "web_call_url": call_record.web_call_url,
            "custom_data": call_record.custom_data,
            "provider": "retell" if is_retell else "vapi"
        }
        if is_retell:
            retell_record = cast(RetellCall, call_record)
            result.update({
                "duration_ms": retell_record.duration_ms,
                "cost": retell_record.cost,
                "disconnection_reason": retell_record.disconnection_reason,
                "latency_ms": retell_record.latency_ms,
                "user_sentiment": retell_record.user_sentiment,
                "call_successful": retell_record.call_successful
            })
        return result
        
    # Otherwise, poll the respective API
    async with httpx.AsyncClient() as client:
        if is_retell and call_record:
            retell_record = cast(RetellCall, call_record)
            response = await client.get(
                f"https://api.retellai.com/v2/get-call/{retell_record.retell_call_id}",
                headers={"Authorization": f"Bearer {settings.retell_api_key}"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                retell_data = response.json()
                retell_status = retell_data.get("call_status")
                
                # Map retell statuses to our standard status
                new_status = call_record.status
                if retell_status in ["ended", "error"]:
                    new_status = "ended"
                elif retell_status == "ongoing":
                    new_status = "in-progress"
                    
                if new_status and (new_status != call_record.status or is_missing_retell_analysis):
                    cast(Any, call_record).status = new_status
                    if new_status == "ended":
                        cast(Any, retell_record).transcript = retell_data.get("transcript") or "No transcript available"
                        cast(Any, retell_record).recording_url = retell_data.get("recording_url")
                        
                        cast(Any, retell_record).duration_ms = retell_data.get("duration_ms")
                        cast(Any, retell_record).disconnection_reason = retell_data.get("disconnection_reason")
                        
                        cost_data = retell_data.get("call_cost")
                        if cost_data:
                            cast(Any, retell_record).cost = cost_data.get("combined_cost")
                            
                        latency_data = retell_data.get("latency")
                        if latency_data and latency_data.get("end_to_end"):
                            cast(Any, retell_record).latency_ms = latency_data.get("end_to_end").get("p90")
                        
                        # Retell provides analysis which contains summary and sentiment
                        analysis = retell_data.get("call_analysis")
                        if analysis:
                            cast(Any, retell_record).summary = analysis.get("call_summary")
                            cast(Any, retell_record).user_sentiment = analysis.get("user_sentiment")
                            cast(Any, retell_record).call_successful = analysis.get("call_successful")
                            cast(Any, retell_record).custom_data = analysis.get("custom_analysis_data")
                        else:
                            cast(Any, retell_record).summary = "No summary available"
                            
                    await session.commit()
            
            result = {
                "status": retell_record.status,
                "transcript": retell_record.transcript,
                "summary": retell_record.summary,
                "recording_url": retell_record.recording_url,
                "web_call_url": retell_record.web_call_url,
                "custom_data": retell_record.custom_data,
                "provider": "retell",
                "duration_ms": retell_record.duration_ms,
                "cost": retell_record.cost,
                "disconnection_reason": retell_record.disconnection_reason,
                "latency_ms": retell_record.latency_ms,
                "user_sentiment": retell_record.user_sentiment,
                "call_successful": retell_record.call_successful
            }
            return result
            
        elif call_record:
            agent_record = cast(AgentCall, call_record)
            response = await client.get(
                f"https://api.vapi.ai/call/{agent_record.vapi_call_id}",
                headers={"Authorization": f"Bearer {settings.vapi_api_key}"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                vapi_data = response.json()
                new_status = vapi_data.get("status")
                
                if new_status and new_status != agent_record.status:
                    cast(Any, agent_record).status = new_status
                    if new_status == "ended":
                        cast(Any, agent_record).transcript = vapi_data.get("transcript")
                        cast(Any, agent_record).summary = vapi_data.get("summary")
                        cast(Any, agent_record).recording_url = vapi_data.get("recordingUrl")
                    await session.commit()
                
            return {
                "status": agent_record.status,
                "transcript": agent_record.transcript,
                "summary": agent_record.summary,
                "recording_url": agent_record.recording_url,
                "web_call_url": agent_record.web_call_url,
                "provider": "vapi"
            }
    return {"status": "none"}
