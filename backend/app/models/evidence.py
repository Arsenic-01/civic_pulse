from sqlalchemy import Column, String, Text, BigInteger, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database.base import Base

class EvidenceModel(Base):
    __tablename__ = "evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    protest_id = Column(UUID(as_uuid=True), ForeignKey("protests.id", ondelete="CASCADE"), nullable=True, index=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey("volunteer_reports.id", ondelete="CASCADE"), nullable=True, index=True)
    
    file_name = Column(String(255), nullable=False)
    storage_key = Column(Text, nullable=False)  # Supabase Storage path
    file_type = Column(String(100), nullable=False)  # MIME type e.g. image/jpeg
    file_size = Column(BigInteger, nullable=False)  # Size in bytes
    
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    captured_at = Column(DateTime(timezone=True), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Database-level check: Exactly one of protest_id or report_id must be present
    __table_args__ = (
        CheckConstraint(
            "(protest_id IS NOT NULL AND report_id IS NULL) OR (protest_id IS NULL AND report_id IS NOT NULL)",
            name="chk_evidence_single_parent"
        ),
    )