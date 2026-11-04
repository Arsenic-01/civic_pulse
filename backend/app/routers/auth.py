from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database.session import get_db
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.models.user import UserModel, RoleEnum
from app.models.report import VolunteerApplicationModel, ApplicationStatusEnum
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest, VolunteerApplicationRequest
from app.schemas.user import UserProfileResponse, UpdateProfileRequest

router = APIRouter(prefix="/auth")

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(UserModel).filter(UserModel.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = UserModel(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        auth_provider="email",
        role=RoleEnum.citizen,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token_data = {"sub": str(user.id)}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == payload.email).first()
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")
    token_data = {"sub": str(user.id)}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshRequest):
    decoded = decode_token(payload.refresh_token)
    if not decoded or decoded.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    token_data = {"sub": decoded["sub"]}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )

@router.post("/logout")
def logout():
    # Stateless JWT — client discards tokens. Future: implement token blocklist.
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserProfileResponse)
def get_me(current_user: UserModel = Depends(get_current_user)):
    return current_user

@router.patch("/me", response_model=UserProfileResponse)
def update_me(
    payload: UpdateProfileRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if payload.username:
        current_user.username = payload.username
    if payload.email:
        existing = db.query(UserModel).filter(UserModel.email == payload.email).first()
        if existing and str(existing.id) != str(current_user.id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")
        current_user.email = payload.email
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/volunteer-application", status_code=status.HTTP_201_CREATED)
def apply_volunteer(
    payload: VolunteerApplicationRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only citizens can apply
    if current_user.role != RoleEnum.citizen:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only citizens can apply to become volunteers")
    # Check if already applied
    existing = db.query(VolunteerApplicationModel).filter(VolunteerApplicationModel.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Application already submitted with status: {existing.status.value}")
    application = VolunteerApplicationModel(
        user_id=current_user.id,
        city=payload.city,
        motivation=payload.motivation,
        experience=payload.experience,
        status=ApplicationStatusEnum.pending,
    )
    db.add(application)
    db.commit()
    return {"message": "Volunteer application submitted. Pending admin review.", "status": "pending"}
