from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class EvidenceResponse(BaseModel):
    id: uuid.UUID
    report_id: Optional[uuid.UUID]
    protest_id: Optional[uuid.UUID]
    file_name: str
    file_type: str
    file_size: int
    storage_key: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}
