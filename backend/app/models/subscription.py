from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.base import Base

class EventSubscriptionModel(Base):
    __tablename__ = "event_subscriptions"

    # Composite Primary Key ensures a user cannot follow the same protest twice
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True)
    protest_id = Column(UUID(as_uuid=True), ForeignKey("protests.id", ondelete="CASCADE"), primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())