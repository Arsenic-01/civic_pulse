from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid
from app.models.user import RoleEnum

class UserProfileResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: Optional[str]
    role: RoleEnum
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

class UpdateProfileRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
