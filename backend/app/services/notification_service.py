"""
Notification Service — creates and delivers in-app notifications.
Call these functions after key state changes (protest status update, report approval, etc.)
"""
from sqlalchemy.orm import Session
from app.models.notification import NotificationModel
from app.models.subscription import EventSubscriptionModel
import uuid


def notify_subscribers(
    db: Session,
    protest_id: uuid.UUID,
    title: str,
    message: str,
) -> int:
    """
    Send a notification to all users subscribed to a protest.
    Returns the number of notifications created.
    """
    subscriptions = db.query(EventSubscriptionModel).filter(
        EventSubscriptionModel.protest_id == protest_id
    ).all()
    notifications = [
        NotificationModel(
            user_id=sub.user_id,
            protest_id=protest_id,
            title=title,
            message=message,
        )
        for sub in subscriptions
    ]
    if notifications:
        db.bulk_save_objects(notifications)
        db.commit()
    return len(notifications)


def notify_user(
    db: Session,
    user_id: uuid.UUID,
    title: str,
    message: str,
    protest_id: uuid.UUID = None,
) -> NotificationModel:
    """Send a targeted notification to a single user."""
    notif = NotificationModel(
        user_id=user_id,
        protest_id=protest_id,
        title=title,
        message=message,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif
