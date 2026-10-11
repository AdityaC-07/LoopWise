import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
from app.models.database import Base


class UserRoleEnum(str, enum.Enum):
    resident = "resident"
    society_manager = "society_manager"
    operator = "operator"
    municipal = "municipal"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    user_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=True, index=True)
    role = Column(Enum(UserRoleEnum, name="userroleenum"), nullable=False, default=UserRoleEnum.resident)
    ward_id = Column(String(32), nullable=True)
    society_id = Column(String(64), nullable=True)
    consent_flags = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    last_active_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    events = relationship("ClassificationEvent", back_populates="user")
