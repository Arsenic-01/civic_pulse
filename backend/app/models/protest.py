from sqlalchemy import Column, String, Text, DateTime, Numeric, Enum as SQLEnum, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum

from app.database.base import Base

class LifecycleStateEnum(str, enum.Enum):
    planned = "planned"
    active = "active"
    dispersing = "dispersing"
    concluded = "concluded"
    relocated = "relocated"
    cancelled = "cancelled"

class VerificationStatusEnum(str, enum.Enum):
    pending = "pending"
    verified = "verified"
    disputed = "disputed"

class ProtestModel(Base):
    __tablename__ = "protests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    location_name = Column(String(255), nullable=False)
    
    # Geospatial coordinates for fast map pin rendering
    latitude = Column(Numeric(precision=9, scale=6), nullable=False)
    longitude = Column(Numeric(precision=9, scale=6), nullable=False)
    city = Column(String(100), nullable=False, default="Pune", index=True)
    
    # States (Indexed for instant filtering on public map & admin dashboard)
    lifecycle_state = Column(SQLEnum(LifecycleStateEnum), nullable=False, default=LifecycleStateEnum.planned, index=True)
    verification_status = Column(SQLEnum(VerificationStatusEnum), nullable=False, default=VerificationStatusEnum.pending, index=True)
    
    # Soft delete support for DELETE /admin/protests/{id} (Archive event)
    is_archived = Column(Boolean, default=False, nullable=False, index=True)
    
    # Timestamps & Timelines
    scheduled_start_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relocation tracking (Links to old protest record if moved)
    relocated_from_id = Column(UUID(as_uuid=True), ForeignKey("protests.id", ondelete="SET NULL"), nullable=True)
    
    # Audit tracking
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True)


class ProtestStatusHistoryModel(Base):
    __tablename__ = "protest_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    protest_id = Column(UUID(as_uuid=True), ForeignKey("protests.id", ondelete="CASCADE"), nullable=False, index=True)
    
    previous_state = Column(SQLEnum(LifecycleStateEnum), nullable=True)
    new_state = Column(SQLEnum(LifecycleStateEnum), nullable=False)
    
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    note = Column(Text, nullable=True)
    
    # If state is 'relocated', points to the newly created protest event
    related_event_id = Column(UUID(as_uuid=True), ForeignKey("protests.id", ondelete="SET NULL"), nullable=True)
    
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)