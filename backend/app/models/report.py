from sqlalchemy import Column, String, Text, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum

from app.database.base import Base

class ReportTypeEnum(str, enum.Enum):
    status_update = "status_update"
    traffic = "traffic"
    medical_assistance = "medical_assistance"
    public_safety = "public_safety"
    accessibility = "accessibility"
    other = "other"

class SourceTypeEnum(str, enum.Enum):
    volunteer = "volunteer"
    official = "official"
    news = "news"
    admin = "admin"

class ModerationStatusEnum(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    needs_review = "needs_review"

class ApplicationStatusEnum(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class VolunteerApplicationModel(Base):
    __tablename__ = "volunteer_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    city = Column(String(100), nullable=False)
    motivation = Column(Text, nullable=False)
    experience = Column(Text, nullable=True)
    
    status = Column(SQLEnum(ApplicationStatusEnum), nullable=False, default=ApplicationStatusEnum.pending, index=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_note = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class VolunteerReportModel(Base):
    __tablename__ = "volunteer_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    protest_id = Column(UUID(as_uuid=True), ForeignKey("protests.id", ondelete="CASCADE"), nullable=True, index=True)
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    
    report_type = Column(SQLEnum(ReportTypeEnum), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    location_name = Column(String(255), nullable=True)
    
    source_type = Column(SQLEnum(SourceTypeEnum), nullable=False, default=SourceTypeEnum.volunteer)
    source_url = Column(Text, nullable=True)
    
    # Indexed for fast public feed polling and admin moderation queue
    moderation_status = Column(SQLEnum(ModerationStatusEnum), nullable=False, default=ModerationStatusEnum.pending, index=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_note = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    occurred_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)