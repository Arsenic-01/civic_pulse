from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from typing import Optional
import uuid

from app.database.session import get_db
from app.core.dependencies import require_admin, require_admin_or_moderator
from app.models.user import UserModel, RoleEnum
from app.models.protest import ProtestModel, ProtestStatusHistoryModel, LifecycleStateEnum, VerificationStatusEnum
from app.models.report import VolunteerReportModel, VolunteerApplicationModel, ModerationStatusEnum, ApplicationStatusEnum
from app.schemas.protest import (
    ProtestCreate, ProtestUpdate, ProtestResponse, ProtestStatusUpdate,
    ProtestRelocate, ProtestStatusHistoryResponse, PaginatedProtests
)
from app.schemas.report import VolunteerApplicationResponse, ApplicationReviewAction

router = APIRouter(prefix="/admin")

# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard/summary")
def dashboard_summary(
    current_user: UserModel = Depends(require_admin_or_moderator()),
    db: Session = Depends(get_db)
):
    def count_protests(state=None):
        q = db.query(func.count(ProtestModel.id)).filter(ProtestModel.is_archived == False)
        if state:
            q = q.filter(ProtestModel.lifecycle_state == state)
        return q.scalar()

    return {
        "total_protests": count_protests(),
        "active_protests": count_protests(LifecycleStateEnum.active),
        "planned_protests": count_protests(LifecycleStateEnum.planned),
        "concluded_protests": count_protests(LifecycleStateEnum.concluded),
        "pending_reports": db.query(func.count(VolunteerReportModel.id)).filter(
            VolunteerReportModel.moderation_status == ModerationStatusEnum.pending
        ).scalar(),
        "disputed_reports": db.query(func.count(VolunteerReportModel.id)).filter(
            VolunteerReportModel.moderation_status == ModerationStatusEnum.needs_review
        ).scalar(),
        "pending_volunteer_applications": db.query(func.count(VolunteerApplicationModel.id)).filter(
            VolunteerApplicationModel.status == ApplicationStatusEnum.pending
        ).scalar(),
    }

# ── Protests CRUD ─────────────────────────────────────────────────────────────

@router.get("/protests", response_model=PaginatedProtests)
def admin_list_protests(
    search: Optional[str] = Query(None),
    lifecycle_state: Optional[LifecycleStateEnum] = Query(None),
    verification_status: Optional[VerificationStatusEnum] = Query(None),
    city: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    current_user: UserModel = Depends(require_admin_or_moderator()),
    db: Session = Depends(get_db)
):
    query = db.query(ProtestModel)
    if search:
        query = query.filter(ProtestModel.name.ilike(f"%{search}%"))
    if lifecycle_state:
        query = query.filter(ProtestModel.lifecycle_state == lifecycle_state)
    if verification_status:
        query = query.filter(ProtestModel.verification_status == verification_status)
    if city:
        query = query.filter(ProtestModel.city.ilike(f"%{city}%"))
    total = query.count()
    items = query.order_by(ProtestModel.updated_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return PaginatedProtests(total=total, page=page, limit=limit, items=items)

@router.post("/protests", response_model=ProtestResponse, status_code=status.HTTP_201_CREATED)
def create_protest(
    payload: ProtestCreate,
    current_user: UserModel = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    protest = ProtestModel(
        name=payload.name,
        description=payload.description,
        location_name=payload.location_name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        city=payload.city,
        scheduled_start_at=payload.scheduled_start_at,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(protest)
    db.commit()
    db.refresh(protest)
    history = ProtestStatusHistoryModel(
        protest_id=protest.id,
        previous_state=None,
        new_state=protest.lifecycle_state,
        changed_by=current_user.id,
        note="Event created",
    )
    db.add(history)
    db.commit()
    return protest

@router.get("/protests/{protest_id}", response_model=ProtestResponse)
def admin_get_protest(
    protest_id: uuid.UUID,
    current_user: UserModel = Depends(require_admin_or_moderator()),
    db: Session = Depends(get_db)
):
    protest = db.query(ProtestModel).filter(ProtestModel.id == protest_id).first()
    if not protest:
        raise HTTPException(status_code=404, detail="Protest not found")
    return protest

@router.patch("/protests/{protest_id}", response_model=ProtestResponse)
def update_protest(
    protest_id: uuid.UUID,
    payload: ProtestUpdate,
    current_user: UserModel = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    protest = db.query(ProtestModel).filter(ProtestModel.id == protest_id).first()
    if not protest:
        raise HTTPException(status_code=404, detail="Protest not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(protest, field, value)
    protest.updated_by = current_user.id
    db.commit()
    db.refresh(protest)
    return protest

@router.delete("/protests/{protest_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_protest(
    protest_id: uuid.UUID,
    current_user: UserModel = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    protest = db.query(ProtestModel).filter(ProtestModel.id == protest_id).first()
    if not protest:
        raise HTTPException(status_code=404, detail="Protest not found")
    protest.is_archived = True
    protest.updated_by = current_user.id
    db.commit()

@router.patch("/protests/{protest_id}/status", response_model=ProtestResponse)
def change_status(
    protest_id: uuid.UUID,
    payload: ProtestStatusUpdate,
    current_user: UserModel = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    protest = db.query(ProtestModel).filter(ProtestModel.id == protest_id).first()
    if not protest:
        raise HTTPException(status_code=404, detail="Protest not found")
    history = ProtestStatusHistoryModel(
        protest_id=protest.id,
        previous_state=protest.lifecycle_state,
        new_state=payload.lifecycle_state,
        changed_by=current_user.id,
        note=payload.note,
    )
    db.add(history)
    protest.lifecycle_state = payload.lifecycle_state
    protest.updated_by = current_user.id
    if payload.lifecycle_state == LifecycleStateEnum.active and not protest.started_at:
        protest.started_at = datetime.now(timezone.utc)
    elif payload.lifecycle_state in (LifecycleStateEnum.concluded, LifecycleStateEnum.cancelled):
        protest.ended_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(protest)
    return protest

@router.post("/protests/{protest_id}/relocate", response_model=ProtestResponse, status_code=status.HTTP_201_CREATED)
def relocate_protest(
    protest_id: uuid.UUID,
    payload: ProtestRelocate,
    current_user: UserModel = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    old_protest = db.query(ProtestModel).filter(ProtestModel.id == protest_id).first()
    if not old_protest:
        raise HTTPException(status_code=404, detail="Protest not found")
    # Archive old location
    old_protest.is_archived = True
    old_protest.lifecycle_state = LifecycleStateEnum.relocated
    old_protest.updated_by = current_user.id
    db.flush()
    # Create new protest at new location
    new_protest = ProtestModel(
        name=old_protest.name,
        description=old_protest.description,
        location_name=payload.new_location_name,
        latitude=payload.new_latitude,
        longitude=payload.new_longitude,
        city=old_protest.city,
        scheduled_start_at=old_protest.scheduled_start_at,
        relocated_from_id=old_protest.id,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(new_protest)
    db.flush()
    # Log history for old protest
    db.add(ProtestStatusHistoryModel(
        protest_id=old_protest.id,
        previous_state=old_protest.lifecycle_state,
        new_state=LifecycleStateEnum.relocated,
        changed_by=current_user.id,
        note=payload.note,
        related_event_id=new_protest.id,
    ))
    db.commit()
    db.refresh(new_protest)
    return new_protest

@router.get("/protests/{protest_id}/history", response_model=list[ProtestStatusHistoryResponse])
def protest_history(
    protest_id: uuid.UUID,
    current_user: UserModel = Depends(require_admin_or_moderator()),
    db: Session = Depends(get_db)
):
    return db.query(ProtestStatusHistoryModel).filter(
        ProtestStatusHistoryModel.protest_id == protest_id
    ).order_by(ProtestStatusHistoryModel.changed_at.asc()).all()

# ── Volunteer Applications ────────────────────────────────────────────────────

@router.get("/volunteer-applications", response_model=list[VolunteerApplicationResponse])
def list_applications(
    app_status: Optional[ApplicationStatusEnum] = Query(None),
    current_user: UserModel = Depends(require_admin_or_moderator()),
    db: Session = Depends(get_db)
):
    query = db.query(VolunteerApplicationModel)
    if app_status:
        query = query.filter(VolunteerApplicationModel.status == app_status)
    return query.order_by(VolunteerApplicationModel.created_at.desc()).all()

@router.patch("/volunteer-applications/{application_id}", response_model=VolunteerApplicationResponse)
def review_application(
    application_id: uuid.UUID,
    payload: ApplicationReviewAction,
    current_user: UserModel = Depends(require_admin_or_moderator()),
    db: Session = Depends(get_db)
):
    application = db.query(VolunteerApplicationModel).filter(VolunteerApplicationModel.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    application.status = payload.action
    application.review_note = payload.review_note
    application.reviewed_by = current_user.id
    application.reviewed_at = datetime.now(timezone.utc)
    # Promote user to volunteer role if approved
    if payload.action == ApplicationStatusEnum.approved:
        user = db.query(UserModel).filter(UserModel.id == application.user_id).first()
        if user:
            user.role = RoleEnum.volunteer
    db.commit()
    db.refresh(application)
    return application

# ── User Management ───────────────────────────────────────────────────────────

@router.get("/users")
def list_users(
    role: Optional[RoleEnum] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    current_user: UserModel = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    query = db.query(UserModel)
    if role:
        query = query.filter(UserModel.role == role)
    if search:
        query = query.filter(
            (UserModel.username.ilike(f"%{search}%")) | (UserModel.email.ilike(f"%{search}%"))
        )
    total = query.count()
    users = query.order_by(UserModel.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return {
        "total": total, "page": page, "limit": limit,
        "items": [{"id": str(u.id), "username": u.username, "email": u.email, "role": u.role.value, "is_active": u.is_active, "created_at": u.created_at} for u in users]
    }

@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: uuid.UUID,
    new_role: RoleEnum,
    current_user: UserModel = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    # Only admin can change roles, and cannot self-demote
    if str(user_id) == str(current_user.id):
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    # Prevent assigning admin via API unless you are admin (already enforced by dependency)
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = new_role
    db.commit()
    return {"message": f"User role updated to {new_role.value}", "user_id": str(user_id)}
