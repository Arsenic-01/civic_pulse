from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
from app.models.report import ReportTypeEnum, ModerationStatusEnum, ApplicationStatusEnum, SourceTypeEnum

class ReportCreate(BaseModel):
    protest_id: uuid.UUID
    report_type: ReportTypeEnum
    title: str
    description: str
    location_name: Optional[str] = None
    occurred_at: Optional[datetime] = None

class ReportUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location_name: Optional[str] = None
    occurred_at: Optional[datetime] = None

class ReportResponse(BaseModel):
    id: uuid.UUID
    protest_id: Optional[uuid.UUID]
    submitted_by: uuid.UUID
    report_type: ReportTypeEnum
    title: str
    description: str
    location_name: Optional[str]
    moderation_status: ModerationStatusEnum
    source_type: SourceTypeEnum
    occurred_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}

class ModerationAction(BaseModel):
    action: ModerationStatusEnum  # approved | rejected | needs_review
    review_note: Optional[str] = None

class VolunteerApplicationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    city: str
    motivation: str
    experience: Optional[str]
    status: ApplicationStatusEnum
    review_note: Optional[str]
    reviewed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}

class ApplicationReviewAction(BaseModel):
    action: ApplicationStatusEnum  # approved | rejected
    review_note: Optional[str] = None
