import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from app.models.database import Base


class UserCorrection(Base):
    __tablename__ = "user_corrections"

    correction_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(PG_UUID(as_uuid=True), ForeignKey("classification_events.event_id"), nullable=False, index=True)
    session_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    corrected_class = Column(String(64), nullable=False)
    correction_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    reviewed = Column(Boolean, default=False, nullable=False)

    # Relationships
    event = relationship("ClassificationEvent", foreign_keys=[event_id])
    user = relationship("User")
