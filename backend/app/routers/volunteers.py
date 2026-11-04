from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid, os, shutil
from datetime import datetime, timezone

from app.database.session import get_db
from app.core.dependencies import get_current_user, require_volunteer
from app.models.user import UserModel, RoleEnum
from app.models.report import VolunteerReportModel, VolunteerApplicationModel, ModerationStatusEnum
from app.models.evidence import EvidenceModel
from app.schemas.report import ReportCreate, ReportUpdate, ReportResponse, VolunteerApplicationResponse
from app.schemas.evidence import EvidenceResponse

router = APIRouter(prefix="/volunteer")

def _assert_volunteer(user: UserModel):
    if user.role not in (RoleEnum.volunteer, RoleEnum.admin, RoleEnum.moderator):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Volunteer access required")

@router.get("/dashboard")
def volunteer_dashboard(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _assert_volunteer(current_user)
    total = db.query(func.count(VolunteerReportModel.id)).filter(VolunteerReportModel.submitted_by == current_user.id).scalar()
    approved = db.query(func.count(VolunteerReportModel.id)).filter(
        VolunteerReportModel.submitted_by == current_user.id,
        VolunteerReportModel.moderation_status == ModerationStatusEnum.approved
    ).scalar()
    pending = db.query(func.count(VolunteerReportModel.id)).filter(
        VolunteerReportModel.submitted_by == current_user.id,
        VolunteerReportModel.moderation_status == ModerationStatusEnum.pending
    ).scalar()
    rejected = db.query(func.count(VolunteerReportModel.id)).filter(
        VolunteerReportModel.submitted_by == current_user.id,
        VolunteerReportModel.moderation_status == ModerationStatusEnum.rejected
    ).scalar()
    return {
        "total_reports": total,
        "approved_reports": approved,
        "pending_reports": pending,
        "rejected_reports": rejected,
    }

@router.get("/applications/me", response_model=VolunteerApplicationResponse)
def my_application(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = db.query(VolunteerApplicationModel).filter(VolunteerApplicationModel.user_id == current_user.id).first()
    if not app:
        raise HTTPException(status_code=404, detail="No volunteer application found")
    return app

@router.get("/reports", response_model=list[ReportResponse])
def my_reports(
    limit: int = Query(50, le=200),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _assert_volunteer(current_user)
    return db.query(VolunteerReportModel).filter(
        VolunteerReportModel.submitted_by == current_user.id
    ).order_by(VolunteerReportModel.created_at.desc()).limit(limit).all()

@router.post("/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def submit_report(
    payload: ReportCreate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _assert_volunteer(current_user)
    report = VolunteerReportModel(
        protest_id=payload.protest_id,
        submitted_by=current_user.id,
        report_type=payload.report_type,
        title=payload.title,
        description=payload.description,
        location_name=payload.location_name,
        occurred_at=payload.occurred_at,
        moderation_status=ModerationStatusEnum.pending,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report

@router.get("/reports/{report_id}", response_model=ReportResponse)
def get_my_report(
    report_id: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _assert_volunteer(current_user)
    report = db.query(VolunteerReportModel).filter(
        VolunteerReportModel.id == report_id,
        VolunteerReportModel.submitted_by == current_user.id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.patch("/reports/{report_id}", response_model=ReportResponse)
def edit_report(
    report_id: uuid.UUID,
    payload: ReportUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _assert_volunteer(current_user)
    report = db.query(VolunteerReportModel).filter(
        VolunteerReportModel.id == report_id,
        VolunteerReportModel.submitted_by == current_user.id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.moderation_status != ModerationStatusEnum.pending:
        raise HTTPException(status_code=400, detail="Only pending reports can be edited")
    if payload.title is not None:
        report.title = payload.title
    if payload.description is not None:
        report.description = payload.description
    if payload.location_name is not None:
        report.location_name = payload.location_name
    if payload.occurred_at is not None:
        report.occurred_at = payload.occurred_at
    db.commit()
    db.refresh(report)
    return report

@router.post("/reports/{report_id}/evidence", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
def upload_evidence(
    report_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _assert_volunteer(current_user)
    report = db.query(VolunteerReportModel).filter(
        VolunteerReportModel.id == report_id,
        VolunteerReportModel.submitted_by == current_user.id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Store file locally (replace with Supabase Storage in production)
    upload_dir = "/tmp/civicpulse_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    storage_key = f"reports/{report_id}/{uuid.uuid4()}_{file.filename}"
    local_path = os.path.join(upload_dir, storage_key.replace("/", "_"))
    with open(local_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    file_size = os.path.getsize(local_path)

    evidence = EvidenceModel(
        report_id=report_id,
        file_name=file.filename,
        storage_key=storage_key,
        file_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        uploaded_by=current_user.id,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence
