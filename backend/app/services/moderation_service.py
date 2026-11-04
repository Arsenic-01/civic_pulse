"""
Moderation Service — workflow helpers for admin/moderator actions.
"""
from sqlalchemy.orm import Session
from app.models.report import VolunteerApplicationModel, ApplicationStatusEnum
from app.models.user import UserModel, RoleEnum
from datetime import datetime, timezone
import uuid


def get_application_or_404(db: Session, application_id: uuid.UUID) -> VolunteerApplicationModel:
    app = db.query(VolunteerApplicationModel).filter(VolunteerApplicationModel.id == application_id).first()
    if not app:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Volunteer application not found")
    return app


def process_application(
    db: Session,
    application: VolunteerApplicationModel,
    action: ApplicationStatusEnum,
    reviewer: UserModel,
    note: str = None,
) -> VolunteerApplicationModel:
    application.status = action
    application.reviewed_by = reviewer.id
    application.review_note = note
    application.reviewed_at = datetime.now(timezone.utc)
    if action == ApplicationStatusEnum.approved:
        user = db.query(UserModel).filter(UserModel.id == application.user_id).first()
        if user and user.role == RoleEnum.citizen:
            user.role = RoleEnum.volunteer
    db.commit()
    db.refresh(application)
    return application
