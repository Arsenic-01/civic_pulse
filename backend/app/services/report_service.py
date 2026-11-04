"""
Report Service — business logic for volunteer report operations.
"""
from sqlalchemy.orm import Session
from app.models.report import VolunteerReportModel, ModerationStatusEnum
from app.models.user import UserModel
from datetime import datetime, timezone
import uuid


def get_report_or_404(db: Session, report_id: uuid.UUID) -> VolunteerReportModel:
    report = db.query(VolunteerReportModel).filter(VolunteerReportModel.id == report_id).first()
    if not report:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Report not found")
    return report


def approve_report(db: Session, report: VolunteerReportModel, reviewer: UserModel, note: str = None) -> VolunteerReportModel:
    report.moderation_status = ModerationStatusEnum.approved
    report.reviewed_by = reviewer.id
    report.review_note = note
    report.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(report)
    return report


def reject_report(db: Session, report: VolunteerReportModel, reviewer: UserModel, note: str = None) -> VolunteerReportModel:
    report.moderation_status = ModerationStatusEnum.rejected
    report.reviewed_by = reviewer.id
    report.review_note = note
    report.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(report)
    return report
