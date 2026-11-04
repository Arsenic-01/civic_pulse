"""
Protest Service — business logic helpers used by admin router.
Separates DB concerns from routing layer.
"""
from sqlalchemy.orm import Session
from app.models.protest import ProtestModel, ProtestStatusHistoryModel, LifecycleStateEnum
from app.models.user import UserModel
import uuid


def get_or_404(db: Session, protest_id: uuid.UUID) -> ProtestModel:
    protest = db.query(ProtestModel).filter(ProtestModel.id == protest_id).first()
    if not protest:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Protest not found")
    return protest


def log_status_change(
    db: Session,
    protest: ProtestModel,
    new_state: LifecycleStateEnum,
    changed_by: uuid.UUID,
    note: str = None,
    related_event_id: uuid.UUID = None,
) -> ProtestStatusHistoryModel:
    entry = ProtestStatusHistoryModel(
        protest_id=protest.id,
        previous_state=protest.lifecycle_state,
        new_state=new_state,
        changed_by=changed_by,
        note=note,
        related_event_id=related_event_id,
    )
    db.add(entry)
    return entry
