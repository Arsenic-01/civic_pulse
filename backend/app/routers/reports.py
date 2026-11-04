from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid

from app.database.session import get_db
from app.core.dependencies import require_admin_or_moderator
from app.models.user import UserModel
from app.models.report import VolunteerReportModel, ModerationStatusEnum
from app.schemas.report import ReportResponse, ModerationAction

router = APIRouter(prefix="/admin/reports")

@router.get("", response_model=list[ReportResponse])
def list_reports(
    moderation_status: ModerationStatusEnum = Query(None),
    protest_id: uuid.UUID = Query(None),
    limit: int = Query(50, le=200),
    page: int = Query(1, ge=1),
    current_user: UserModel = Depends(require_admin_or_moderator()),
    db: Session = Depends(get_db)
):
    query = db.query(VolunteerReportModel)
    if moderation_status:
        query = query.filter(VolunteerReportModel.moderation_status == moderation_status)
    if protest_id:
        query = query.filter(VolunteerReportModel.protest_id == protest_id)
    return query.order_by(VolunteerReportModel.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: uuid.UUID,
    current_user: UserModel = Depends(require_admin_or_moderator()),
    db: Session = Depends(get_db)
):
    report = db.query(VolunteerReportModel).filter(VolunteerReportModel.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.patch("/{report_id}/review", response_model=ReportResponse)
def review_report(
    report_id: uuid.UUID,
    payload: ModerationAction,
    current_user: UserModel = Depends(require_admin_or_moderator()),
    db: Session = Depends(get_db)
):
    report = db.query(VolunteerReportModel).filter(VolunteerReportModel.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.moderation_status = payload.action
    report.review_note = payload.review_note
    report.reviewed_by = current_user.id
    report.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(report)
    return report
