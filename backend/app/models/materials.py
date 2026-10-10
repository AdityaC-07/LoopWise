from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Boolean, Enum
from app.models.database import Base
from app.models.events import MaterialCategoryEnum, DisposalBinEnum, RecoveryPotentialEnum


class Material(Base):
    __tablename__ = "materials"

    material_id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    category = Column(Enum(MaterialCategoryEnum, name="materialcategoryenum"), nullable=False)
    subcategory = Column(String(64), nullable=True)
    disposal_bin = Column(Enum(DisposalBinEnum, name="disposalbinenum"), nullable=False)
    recovery_potential = Column(Enum(RecoveryPotentialEnum, name="recoverypotentialenum"), nullable=False)
    next_life = Column(Text, nullable=True)
    recovery_channel = Column(String(64), nullable=True)
    contamination_notes = Column(Text, nullable=True)
    icon_slug = Column(String(64), nullable=True)
    demo_seed = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
