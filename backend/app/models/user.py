from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum

from app.database.base import Base

class RoleEnum(str, enum.Enum):
    citizen = "citizen"
    volunteer = "volunteer"
    moderator = "moderator"
    admin = "admin"

class UserModel(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=True)  # For email/password auth
    auth_provider = Column(String(30), nullable=False, default="email")  # google, email, etc.
    auth_subject = Column(String(255), nullable=True)  # Provider-specific user ID
    
    role = Column(SQLEnum(RoleEnum), nullable=False, default=RoleEnum.citizen)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())