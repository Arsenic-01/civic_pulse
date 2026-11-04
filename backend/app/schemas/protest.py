from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
import uuid
from app.models.protest import LifecycleStateEnum, VerificationStatusEnum

class ProtestCreate(BaseModel):
    name: str
    description: Optional[str] = None
    location_name: str
    latitude: Decimal
    longitude: Decimal
    city: str = "Pune"
    scheduled_start_at: Optional[datetime] = None

class ProtestUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    city: Optional[str] = None
    scheduled_start_at: Optional[datetime] = None

class ProtestStatusUpdate(BaseModel):
    lifecycle_state: LifecycleStateEnum
    note: Optional[str] = None

class ProtestRelocate(BaseModel):
    new_location_name: str
    new_latitude: Decimal
    new_longitude: Decimal
    note: Optional[str] = None

class ProtestResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    location_name: str
    latitude: Decimal
    longitude: Decimal
    city: str
    lifecycle_state: LifecycleStateEnum
    verification_status: VerificationStatusEnum
    is_archived: bool
    scheduled_start_at: Optional[datetime]
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class ProtestMapMarker(BaseModel):
    id: uuid.UUID
    name: str
    latitude: Decimal
    longitude: Decimal
    lifecycle_state: LifecycleStateEnum
    city: str

    model_config = {"from_attributes": True}

class ProtestStatusHistoryResponse(BaseModel):
    id: uuid.UUID
    previous_state: Optional[LifecycleStateEnum]
    new_state: LifecycleStateEnum
    note: Optional[str]
    changed_at: datetime

    model_config = {"from_attributes": True}

class PaginatedProtests(BaseModel):
    total: int
    page: int
    limit: int
    items: List[ProtestResponse]
