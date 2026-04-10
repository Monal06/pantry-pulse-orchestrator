from __future__ import annotations

from fastapi import APIRouter, Query

from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])

DEFAULT_USER = "demo-user"


@router.get("/check")
async def check_alerts(user_id: str = Query(default=DEFAULT_USER)):
    """Check for freshness alerts. Call this periodically from the client app."""
    alerts = await notification_service.check_freshness_alerts(user_id)
    return {"alerts": alerts, "count": len(alerts)}


@router.get("/history")
async def get_history(user_id: str = Query(default=DEFAULT_USER)):
    """Get notification history."""
    return await notification_service.get_notification_history(user_id)
