from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import uuid

from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import UserModel
from app.models.notification import NotificationModel
from app.models.subscription import EventSubscriptionModel
from app.models.protest import ProtestModel

router = APIRouter()

# ── Subscriptions ─────────────────────────────────────────────────────────────

@router.post("/subscriptions", status_code=status.HTTP_201_CREATED)
def follow_protest(
    protest_id: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    protest = db.query(ProtestModel).filter(ProtestModel.id == protest_id).first()
    if not protest:
        raise HTTPException(status_code=404, detail="Protest not found")
    existing = db.query(EventSubscriptionModel).filter(
        EventSubscriptionModel.user_id == current_user.id,
        EventSubscriptionModel.protest_id == protest_id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Already following this protest")
    sub = EventSubscriptionModel(user_id=current_user.id, protest_id=protest_id)
    db.add(sub)
    db.commit()
    return {"message": "Now following protest"}

@router.get("/subscriptions")
def list_subscriptions(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    subs = db.query(EventSubscriptionModel).filter(EventSubscriptionModel.user_id == current_user.id).all()
    return [{"protest_id": str(s.protest_id), "created_at": s.created_at} for s in subs]

@router.delete("/subscriptions/{protest_id}", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_protest(
    protest_id: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sub = db.query(EventSubscriptionModel).filter(
        EventSubscriptionModel.user_id == current_user.id,
        EventSubscriptionModel.protest_id == protest_id
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    db.delete(sub)
    db.commit()

# ── Notifications ─────────────────────────────────────────────────────────────

@router.get("/notifications")
def get_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, le=200),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(NotificationModel).filter(NotificationModel.user_id == current_user.id)
    if unread_only:
        query = query.filter(NotificationModel.is_read == False)
    return query.order_by(NotificationModel.created_at.desc()).limit(limit).all()

@router.patch("/notifications/{notification_id}/read")
def mark_read(
    notification_id: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notif = db.query(NotificationModel).filter(
        NotificationModel.id == notification_id,
        NotificationModel.user_id == current_user.id
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()
    return {"message": "Marked as read"}
