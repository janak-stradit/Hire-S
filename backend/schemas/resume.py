from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResumeRead(BaseModel):
    resume_id: str
    candidate_id: str
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    storage_path: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)

