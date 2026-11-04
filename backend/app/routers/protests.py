from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
import uuid

from app.database.session import get_db
from app.models.protest import ProtestModel, ProtestStatusHistoryModel, LifecycleStateEnum, VerificationStatusEnum
from app.models.report import VolunteerReportModel, ModerationStatusEnum
from app.schemas.protest import ProtestResponse, ProtestMapMarker, ProtestStatusHistoryResponse, PaginatedProtests
from app.schemas.report import ReportResponse

router = APIRouter(prefix="/protests")

@router.get("", response_model=PaginatedProtests)
def list_protests(
    city: Optional[str] = Query(None),
    status: Optional[LifecycleStateEnum] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(ProtestModel).filter(ProtestModel.is_archived == False)
    if city:
        query = query.filter(ProtestModel.city.ilike(f"%{city}%"))
    if status:
        query = query.filter(ProtestModel.lifecycle_state == status)
    if search:
        query = query.filter(ProtestModel.name.ilike(f"%{search}%"))
    total = query.count()
    items = query.order_by(ProtestModel.updated_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return PaginatedProtests(total=total, page=page, limit=limit, items=items)

@router.get("/map", response_model=list[ProtestMapMarker])
def map_markers(
    city: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(ProtestModel).filter(
        ProtestModel.is_archived == False,
        ProtestModel.lifecycle_state.in_([LifecycleStateEnum.planned, LifecycleStateEnum.active, LifecycleStateEnum.dispersing])
    )
    if city:
        query = query.filter(ProtestModel.city.ilike(f"%{city}%"))
    return query.all()

@router.get("/{protest_id}", response_model=ProtestResponse)
def get_protest(protest_id: uuid.UUID, db: Session = Depends(get_db)):
    protest = db.query(ProtestModel).filter(ProtestModel.id == protest_id, ProtestModel.is_archived == False).first()
    if not protest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Protest not found")
    return protest

@router.get("/{protest_id}/timeline", response_model=list[ProtestStatusHistoryResponse])
def get_timeline(protest_id: uuid.UUID, db: Session = Depends(get_db)):
    protest = db.query(ProtestModel).filter(ProtestModel.id == protest_id).first()
    if not protest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Protest not found")
    return db.query(ProtestStatusHistoryModel).filter(
        ProtestStatusHistoryModel.protest_id == protest_id
    ).order_by(ProtestStatusHistoryModel.changed_at.asc()).all()

@router.get("/{protest_id}/updates", response_model=list[ReportResponse])
def get_approved_updates(protest_id: uuid.UUID, db: Session = Depends(get_db)):
    protest = db.query(ProtestModel).filter(ProtestModel.id == protest_id).first()
    if not protest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Protest not found")
    return db.query(VolunteerReportModel).filter(
        VolunteerReportModel.protest_id == protest_id,
        VolunteerReportModel.moderation_status == ModerationStatusEnum.approved
    ).order_by(VolunteerReportModel.created_at.desc()).all()
