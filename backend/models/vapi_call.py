from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base

class VapiCall(Base):
    __tablename__ = "vapi_calls"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    application_id: Mapped[str] = mapped_column(String(36), ForeignKey("applications.application_id", ondelete="CASCADE"), nullable=False, index=True)
    vapi_call_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    web_call_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="queued") # queued, in-progress, ended, failed
    transcript: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    recording_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    application = relationship("Application", backref="vapi_calls")
