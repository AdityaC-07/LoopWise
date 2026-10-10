import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, Text, DateTime, ForeignKey, Index, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
from app.models.database import Base


class InputTypeEnum(str, enum.Enum):
    image = "image"
    text = "text"


class MaterialCategoryEnum(str, enum.Enum):
    plastic = "plastic"
    glass = "glass"
    metal = "metal"
    organic = "organic"
    paper = "paper"
    e_waste = "e_waste"
    composite = "composite"
    hazardous = "hazardous"
    other = "other"


class DisposalBinEnum(str, enum.Enum):
    wet = "wet"
    dry = "dry"
    hazardous = "hazardous"
    e_waste = "e_waste"
    rejected = "rejected"


class RecoveryPotentialEnum(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"
    none = "none"


class ClassificationEvent(Base):
    __tablename__ = "classification_events"

    event_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    ward_id = Column(String(32), nullable=True, index=True)
    input_type = Column(Enum(InputTypeEnum, name="inputtypeenum"), nullable=False)
    model_version = Column(String(32), nullable=False, default="mock-v1")
    predicted_class = Column(String(64), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    top3_predictions = Column(JSON, nullable=True)
    material_category = Column(Enum(MaterialCategoryEnum, name="materialcategoryenum"), nullable=False)
    disposal_bin = Column(Enum(DisposalBinEnum, name="disposalbinenum"), nullable=False)
    recovery_potential = Column(Enum(RecoveryPotentialEnum, name="recoverypotentialenum"), nullable=False)
    recovery_channel = Column(String(64), nullable=True)
    is_corrected = Column(Boolean, default=False, nullable=False, index=True)
    correction_id = Column(PG_UUID(as_uuid=True), ForeignKey("user_corrections.correction_id"), nullable=True)
    image_stored = Column(Boolean, default=False, nullable=False)
    image_key = Column(Text, nullable=True)
    consent_flags = Column(JSON, nullable=True)
    demo_mode = Column(Boolean, default=False, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="events")
    correction = relationship("UserCorrection", foreign_keys=[correction_id], post_update=True)

    __table_args__ = (
        Index("idx_events_ward_created", "ward_id", "created_at"),
        Index("idx_events_session_created", "session_id", "created_at"),
        Index("idx_events_class_created", "predicted_class", "created_at"),
        Index("idx_events_corrected_created", "is_corrected", "created_at"),
        Index("idx_events_demo_created", "demo_mode", "created_at"),
    )
