from __future__ import annotations

from fastapi import APIRouter, Query

from app.models.waste import WasteEventType, WasteStats
from app.services import waste_service

router = APIRouter(prefix="/waste", tags=["waste"])

DEFAULT_USER = "demo-user"


@router.get("/stats", response_model=WasteStats)
async def get_waste_stats(user_id: str = Query(default=DEFAULT_USER)):
    """Get waste tracking statistics: items saved/wasted, money saved, CO2 impact, trends."""
    return await waste_service.get_stats(user_id)


@router.get("/events")
async def get_waste_events(user_id: str = Query(default=DEFAULT_USER)):
    """Get all waste tracking events."""
    events = await waste_service.get_events(user_id)
    return [e.model_dump(mode="json") for e in events]


@router.post("/log")
async def log_waste_event(
    item_name: str = Query(...),
    category: str = Query(default="other"),
    event_type: WasteEventType = Query(...),
    quantity: float = Query(default=1.0, gt=0),
    user_id: str = Query(default=DEFAULT_USER),
):
    """Manually log a waste event (saved, wasted, frozen, donated)."""
    event = await waste_service.log_event(user_id, item_name, category, event_type, quantity)
    return event.model_dump(mode="json")
