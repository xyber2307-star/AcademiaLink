from datetime import datetime, timezone
import logging
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user
from app.firebase import get_db
from app.models import (
    NotificationItem,
    NotificationListResponse,
    NotificationType,
    UserProfileResponse,
)

logger = logging.getLogger("academialink.notifications")

router = APIRouter(prefix="/notifications", tags=["Notifications & Activity"])


def create_notification(
    db,
    uid: str,
    n_type: NotificationType,
    title: str,
    message: str,
    related_id: Optional[str] = None,
) -> Optional[str]:
    """Helper to dispatch real event-driven notifications to users/{uid}/notifications."""
    try:
        notification_id = f"notif_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        notif_doc = {
            "notification_id": notification_id,
            "uid": uid,
            "type": n_type,
            "title": title,
            "message": message,
            "read": False,
            "created_at": now_iso,
            "related_id": related_id,
            "provenance": {
                "source": "activity_system",
                "data_status": "available",
                "retrieved_at": now_iso,
                "is_test_data": False,
            },
        }
        db.collection("users").document(uid).collection("notifications").document(notification_id).set(notif_doc)
        logger.info("Dispatched notification %s to user %s: %s", notification_id, uid, title)
        return notification_id
    except Exception as e:
        logger.error("Failed to dispatch notification to user %s: %s", uid, e)
        return None


@router.get("/me", response_model=NotificationListResponse, summary="Get notifications for current user")
async def get_my_notifications(
    limit: int = 50,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """Retrieve all notifications for the authenticated user."""
    db = get_db()
    notifs_ref = db.collection("users").document(current_user.uid).collection("notifications")
    docs = notifs_ref.stream()

    items = []
    unread_count = 0
    for doc in docs:
        d = doc.to_dict() or {}
        if not d.get("notification_id"):
            d["notification_id"] = doc.id
        if not d.get("uid"):
            d["uid"] = current_user.uid
        if not d.get("read", False):
            unread_count += 1
        items.append(NotificationItem(**d))

    # Sort descending by created_at
    items.sort(key=lambda x: x.created_at or "", reverse=True)
    items = items[:limit]

    return NotificationListResponse(notifications=items, unread_count=unread_count)


@router.patch("/{notification_id}/read", summary="Mark notification as read")
async def mark_notification_read(
    notification_id: str,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """Marks a specific notification as read. Users can only modify their own notifications."""
    db = get_db()
    doc_ref = db.collection("users").document(current_user.uid).collection("notifications").document(notification_id)
    snap = doc_ref.get()
    if not snap.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification '{notification_id}' not found.",
        )
    doc_ref.update({"read": True})
    return {"status": "success", "notification_id": notification_id, "read": True}


@router.post("/mark-all-read", summary="Mark all notifications as read")
async def mark_all_notifications_read(
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """Marks all notifications for current user as read."""
    db = get_db()
    notifs_ref = db.collection("users").document(current_user.uid).collection("notifications")
    docs = notifs_ref.stream()
    count = 0
    for doc in docs:
        d = doc.to_dict() or {}
        if not d.get("read", False):
            doc.reference.update({"read": True})
            count += 1

    return {"status": "success", "marked_read_count": count}
