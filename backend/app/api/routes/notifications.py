"""Notifications routes — in-app tray and mark as read."""
from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database.session import get_db
from app.models.notification import Notification, NotificationChannel
from app.models.user import User
from app.schemas.analytics import NotificationResponse, MarkReadRequest

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationResponse])
async def get_notifications(
    channel: str = "IN_APP",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Notification).where(Notification.user_id == current_user.id)
    if channel == "IN_APP":
        q = q.where(Notification.channel == NotificationChannel.IN_APP)
    result = await db.execute(q.order_by(Notification.created_at.desc()).limit(50))
    return result.scalars().all()


@router.post("/read")
async def mark_notifications_read(
    req: MarkReadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Notification)
        .where(
            Notification.id.in_(req.notification_ids),
            Notification.user_id == current_user.id,
        )
        .values(is_read=True)
    )
    return {"marked_read": len(req.notification_ids)}
