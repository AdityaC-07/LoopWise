import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Date, DateTime, JSON, UniqueConstraint
from app.models.database import Base


class WardAnalyticsRollup(Base):
    __tablename__ = "ward_analytics_rollups"

    rollup_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ward_id = Column(String(32), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    total_events = Column(Integer, default=0, nullable=False)
    unique_sessions = Column(Integer, default=0, nullable=False)
    correction_rate = Column(Float, default=0.0, nullable=False)
    contamination_rate = Column(Float, default=0.0, nullable=False)
    recovery_potential_avg = Column(Float, default=0.0, nullable=False)
    low_confidence_rate = Column(Float, default=0.0, nullable=False)
    material_breakdown = Column(JSON, nullable=True)
    top_misclassifications = Column(JSON, nullable=True)
    computed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("ward_id", "date", name="uq_ward_date"),
    )
