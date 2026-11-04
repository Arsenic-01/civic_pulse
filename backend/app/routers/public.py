from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from typing import Optional

from app.database.session import get_db
from app.models.protest import ProtestModel, LifecycleStateEnum
from app.models.report import VolunteerReportModel, ModerationStatusEnum
from app.schemas.report import ReportResponse

router = APIRouter(prefix="/public")

@router.get("/stats")
def public_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(ProtestModel.id)).filter(ProtestModel.is_archived == False).scalar()
    active = db.query(func.count(ProtestModel.id)).filter(
        ProtestModel.is_archived == False,
        ProtestModel.lifecycle_state == LifecycleStateEnum.active
    ).scalar()
    planned = db.query(func.count(ProtestModel.id)).filter(
        ProtestModel.is_archived == False,
        ProtestModel.lifecycle_state == LifecycleStateEnum.planned
    ).scalar()
    concluded = db.query(func.count(ProtestModel.id)).filter(
        ProtestModel.is_archived == False,
        ProtestModel.lifecycle_state == LifecycleStateEnum.concluded
    ).scalar()
    return {
        "total_protests": total,
        "active_protests": active,
        "planned_protests": planned,
        "concluded_protests": concluded,
    }

@router.get("/feed", response_model=list[ReportResponse])
def public_feed(
    since: Optional[datetime] = Query(None, description="ISO 8601 timestamp — returns only updates after this time"),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(VolunteerReportModel).filter(
        VolunteerReportModel.moderation_status == ModerationStatusEnum.approved
    )
    if since:
        query = query.filter(VolunteerReportModel.created_at > since)
    return query.order_by(VolunteerReportModel.created_at.desc()).limit(limit).all()
