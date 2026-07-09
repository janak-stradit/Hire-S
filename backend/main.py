"""FastAPI composition root for HireX.

This file is intentionally kept small: it wires infrastructure-level concerns
(settings, CORS, and route registration) and then delegates all business logic
to domain routers and services. The frontend talks to these `/api/*` prefixes
through `frontend/src/api/client.ts`.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.applications.routes import router as applications_router
from backend.api.admin.routes import router as admin_router
from backend.api.admin.vapi_config import router as vapi_config_router
from backend.api.admin.vapi_calls import router as vapi_calls_router
from backend.api.auth.routes import router as auth_router
from backend.api.candidate.routes import router as candidate_router
from backend.api.excel_intake.routes import router as excel_intake_router
from backend.api.jobs.routes import router as jobs_router
from backend.api.resumes.routes import router as resumes_router
from backend.api.validator.routes import router as validator_router
from backend.api.resume_intake.routes import router as resume_intake_router
from backend.api.talent_pool.routes import router as talent_pool_router
from backend.config.settings import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")

# Local MVP CORS policy: the Next.js development server runs on port 3000 and
# calls the FastAPI server on port 8000. Production should replace this with the
# deployed frontend origin list.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000", "http://127.0.0.1:3001", "http://localhost:3001", "http://localhost:3002", "http://127.0.0.1:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route boundaries map directly to product areas:
# auth/candidate/resume/job/application are the foundation workflow,
# excel-intake and validator are the screening engine, and admin/talent-pool
# power HR operations plus reusable candidate metadata.
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(candidate_router, prefix="/api/candidates", tags=["candidates"])
app.include_router(resumes_router, prefix="/api/resumes", tags=["resumes"])
app.include_router(jobs_router, prefix="/api/jobs", tags=["jobs"])
app.include_router(applications_router, prefix="/api/applications", tags=["applications"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(vapi_config_router, prefix="/api/admin")
app.include_router(vapi_calls_router, prefix="/api/admin")
app.include_router(validator_router, prefix="/api/validator", tags=["validator"])
app.include_router(excel_intake_router, prefix="/api/excel-intake", tags=["excel-intake"])
app.include_router(talent_pool_router, prefix="/api/talent-pool", tags=["talent-pool"])
app.include_router(resume_intake_router, prefix="/api/resume-intake", tags=["resume-intake"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
