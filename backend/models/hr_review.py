from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class HRReviewAction(Base):
    __tablename__ = "hr_review_actions"

    action_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    application_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("applications.application_id", ondelete="CASCADE"), index=True
    )
    validator_result_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("validator_results.validator_result_id"), index=True
    )
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    reason_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    actor_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    application = relationship("Application")
    validator_result = relationship("ValidatorResult")
    actor = relationship("User")
