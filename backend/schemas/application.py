from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ApplicationCreate(BaseModel):
    job_id: str


class ApplicationRead(BaseModel):
    application_id: str
    candidate_id: str
    job_id: str
    application_status: str
    applied_at: datetime

    model_config = ConfigDict(from_attributes=True)

