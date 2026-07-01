"""Excel/JD intake API used by the HR operations dashboard.

MVP sourcing is file-based: HR selects a JD workbook row and a candidate pool
workbook, then this router calls `ExcelIntakeService` to create a validator
batch. Later Naukri/LinkedIn/ATS connectors can reuse the same service contract
after replacing the workbook reader adapter.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user
from backend.database.session import get_session
from pathlib import Path

from backend.excel_intake.contracts import (
    CandidatePoolSummary,
    ExcelIntakeConfiguration,
    ExcelIntakeRequest,
    ExcelIntakeResult,
    RequirementUpsertRequest,
    RequirementStatusRequest,
)
from backend.excel_intake.service import CANDIDATE_POOL_FILES, ExcelIntakeService
from backend.excel_intake.workbooks import (
    REQUIREMENT_UPLOAD_CONTENT_TYPES,
    REQUIREMENT_UPLOAD_EXTENSIONS,
    WorkbookValidationError,
    import_requirements,
    list_requirements,
    read_requirement,
    read_candidates,
    update_requirement_status,
    upsert_requirement,
)
from backend.models.user import User
from backend.services.requirement_scan_service import RequirementScanService

router = APIRouter()
PROJECT_ROOT = Path(__file__).resolve().parents[3]
REQUIREMENT_WORKBOOK = PROJECT_ROOT / "storage/job_requirements/jd_input.xlsx"
MAX_BULK_REQUIREMENT_UPLOAD_BYTES = 10 * 1024 * 1024
def require_manager(user: User) -> None:
    """Restrict JD management and validator execution to hiring operators."""
    if user.role not in {"recruiter", "hr", "admin"}:
        raise HTTPException(status_code=403, detail="Job manager role required")


@router.get("/configuration", response_model=ExcelIntakeConfiguration)
async def configuration(current_user: User = Depends(get_current_user)):
    # Frontend calls this on page load to populate JD dropdowns and candidate
    # source choices before the Run Validator button is enabled.
    require_manager(current_user)
    pools = []
    for pool, details in CANDIDATE_POOL_FILES.items():
        path = PROJECT_ROOT / details["path"]
        include_synthetic = bool(details["include_synthetic"])
        try:
            selected, skipped = read_candidates(path, include_synthetic=include_synthetic)
            total_rows = len(selected) + skipped
            eligible_rows = len(selected)
        except (WorkbookValidationError, FileNotFoundError, Exception):
            total_rows = 0
            eligible_rows = 0
        pools.append(CandidatePoolSummary(
            pool=pool, label=str(details["label"]), workbook=str(path.relative_to(PROJECT_ROOT)),
            total_rows=total_rows, eligible_rows=eligible_rows,
            simulation_only=bool(details["simulation_only"]),
        ))
    try:
        requirements = list_requirements(REQUIREMENT_WORKBOOK)
    except (WorkbookValidationError, FileNotFoundError, Exception):
        requirements = []
    return ExcelIntakeConfiguration(requirements=requirements, candidate_pools=pools)


@router.post("/requirements", response_model=RequirementUpsertRequest)
async def save_requirement(
    payload: RequirementUpsertRequest,
    current_user: User = Depends(get_current_user),
):
    # JD rows are stored in the MVP workbook so non-technical HR users can edit
    # requirements without touching code or database migrations.
    require_manager(current_user)
    upsert_requirement(REQUIREMENT_WORKBOOK, payload, payload.created_by or current_user.email)
    return payload


@router.get("/requirements/{requirement_id}")
async def get_requirement(
    requirement_id: str,
    current_user: User = Depends(get_current_user),
):
    require_manager(current_user)
    try:
        return read_requirement(REQUIREMENT_WORKBOOK, requirement_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/requirements/{requirement_id}/scan")
async def scan_requirement(
    requirement_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    require_manager(current_user)
    try:
        requirement = read_requirement(REQUIREMENT_WORKBOOK, requirement_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return await RequirementScanService(session).scan(requirement)


@router.post("/requirements/bulk-upload")
async def bulk_upload_requirements(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    # Batch JD creation path. HR uploads a CSV/XLSX in the standard JD column
    # format; each row is validated and then upserted into the JD workbook.
    require_manager(current_user)
    filename = file.filename or ""
    suffix = Path(filename).suffix.lower()
    if suffix not in REQUIREMENT_UPLOAD_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are allowed (.csv, .xlsx, .xlsm)")
    # Trust the file extension over content-type — browsers often report
    # application/octet-stream for xlsx files uploaded via <input type="file">.
    _generic_types = {"application/octet-stream", "binary/octet-stream", ""}
    if (
        file.content_type
        and file.content_type not in REQUIREMENT_UPLOAD_CONTENT_TYPES
        and file.content_type not in _generic_types
    ):
        raise HTTPException(status_code=400, detail="Unsupported file content type for bulk JD upload")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded JD file is empty")
    if len(content) > MAX_BULK_REQUIREMENT_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="Bulk JD upload file is too large. Maximum size is 10 MB")
    try:
        return import_requirements(
            REQUIREMENT_WORKBOOK,
            filename,
            content,
            current_user.email,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/requirements/{requirement_id}/status")
async def set_requirement_status(
    requirement_id: str,
    payload: RequirementStatusRequest,
    current_user: User = Depends(get_current_user),
):
    # Status controls which JD is active/draft/inactive in the dashboard.
    require_manager(current_user)
    return update_requirement_status(REQUIREMENT_WORKBOOK, requirement_id, payload.status)


@router.post("/run", response_model=ExcelIntakeResult)
async def run_excel_intake(
    payload: ExcelIntakeRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Start-to-end path: frontend button -> this endpoint -> ExcelIntakeService
    # -> candidate identity dedupe -> validator scoring -> batch dashboard.
    return await ExcelIntakeService(session).run(current_user, payload)


def batch_response(batch):
    """Return a stable batch DTO for dashboard tables and details."""
    return {
        "batch_id": batch.batch_id, "requirement_id": batch.requirement_id,
        "job_id": batch.job_id, "status": batch.status,
        "candidates_read": batch.candidates_read, "candidates_imported": batch.candidates_imported,
        "candidates_skipped": batch.candidates_skipped, "pass_count": batch.pass_count,
        "review_count": batch.review_count, "fail_count": batch.fail_count,
        "candidate_workbook": batch.candidate_workbook,
        "requirement_workbook": batch.requirement_workbook,
        "shortlisted_workbook": batch.shortlisted_workbook, "error_report": batch.error_report,
        "started_at": batch.started_at, "completed_at": batch.completed_at,
    }


@router.get("/batches/latest")
async def get_latest_excel_intake_batch(
    requirement_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    require_manager(current_user)
    batch = await ExcelIntakeService(session).get_latest_batch(requirement_id)
    if not batch:
        raise HTTPException(status_code=404, detail="No validator batch exists for this requirement")
    return batch_response(batch)


@router.get("/batches")
async def list_excel_intake_batches(
    requirement_id: str | None = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    require_manager(current_user)
    batches = await ExcelIntakeService(session).list_batches(requirement_id)
    return [batch_response(batch) for batch in batches]


@router.get("/batches/{batch_id}")
async def get_excel_intake_batch(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    require_manager(current_user)
    batch = await ExcelIntakeService(session).get_batch(batch_id)
    return batch_response(batch)


@router.delete("/batches/{batch_id}")
async def delete_excel_intake_batch(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    require_manager(current_user)
    return await ExcelIntakeService(session).delete_batch(batch_id)
