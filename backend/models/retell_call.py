from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base

class RetellCall(Base):
    __tablename__ = "retell_calls"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    application_id: Mapped[str] = mapped_column(String(36), ForeignKey("applications.application_id", ondelete="CASCADE"), nullable=False, index=True)
    retell_call_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    web_call_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="registered") # registered, ongoing, ended, error
    
    transcript: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    recording_url: Mapped[str | None] = mapped_column(Text)
    custom_data: Mapped[dict | None] = mapped_column(JSON)
    
    # Detailed Retell Analytics
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    cost: Mapped[float | None] = mapped_column(Float)
    disconnection_reason: Mapped[str | None] = mapped_column(String(100))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    user_sentiment: Mapped[str | None] = mapped_column(String(50))
    call_successful: Mapped[bool | None] = mapped_column(Boolean)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    application = relationship("Application", backref="retell_calls")
