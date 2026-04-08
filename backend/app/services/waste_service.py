from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from uuid import uuid4

from app.models.waste import (
    AVG_PRICE_PER_CATEGORY,
    CO2_KG_PER_FOOD_ITEM,
    WasteEvent,
    WasteEventType,
    WasteStats,
)

_events: dict[str, list[WasteEvent]] = {}


async def log_event(
    user_id: str,
    item_name: str,
    category: str,
    event_type: WasteEventType,
    quantity: float = 1.0,
) -> WasteEvent:
    price = AVG_PRICE_PER_CATEGORY.get(category, 3.0) * quantity
    co2 = CO2_KG_PER_FOOD_ITEM * quantity if event_type == WasteEventType.SAVED else 0.0

    event = WasteEvent(
        id=str(uuid4()),
        user_id=user_id,
        item_name=item_name,
        category=category,
        event_type=event_type,
        quantity=quantity,
        estimated_value=round(price, 2),
        co2_saved_kg=round(co2, 2),
        date=date.today(),
    )
    _events.setdefault(user_id, []).append(event)
    return event


async def get_events(user_id: str) -> list[WasteEvent]:
    return _events.get(user_id, [])


async def get_stats(user_id: str) -> WasteStats:
    events = _events.get(user_id, [])

    saved = [e for e in events if e.event_type == WasteEventType.SAVED]
    wasted = [e for e in events if e.event_type == WasteEventType.WASTED]
    frozen = [e for e in events if e.event_type == WasteEventType.FROZEN]

    total_saved = len(saved)
    total_wasted = len(wasted)
    total_frozen = len(frozen)
    total = total_saved + total_wasted

    money_saved = sum(e.estimated_value for e in saved)
    money_wasted = sum(e.estimated_value for e in wasted)
    co2_saved = sum(e.co2_saved_kg for e in saved)

    save_rate = (total_saved / total * 100) if total > 0 else 0.0

    # Weekly trend for the last 4 weeks
    weekly_trend = []
    today = date.today()
    for week_offset in range(3, -1, -1):
        week_start = today - timedelta(days=today.weekday() + 7 * week_offset)
        week_end = week_start + timedelta(days=6)
        week_saved = sum(
            1 for e in saved if week_start <= e.date <= week_end
        )
        week_wasted = sum(
            1 for e in wasted if week_start <= e.date <= week_end
        )
        weekly_trend.append({
            "week_start": str(week_start),
            "saved": week_saved,
            "wasted": week_wasted,
        })

    # Category breakdown
    cat_breakdown: dict[str, dict] = defaultdict(lambda: {"saved": 0, "wasted": 0, "value": 0.0})
    for e in saved:
        cat_breakdown[e.category]["saved"] += 1
        cat_breakdown[e.category]["value"] += e.estimated_value
    for e in wasted:
        cat_breakdown[e.category]["wasted"] += 1

    return WasteStats(
        total_items_saved=total_saved,
        total_items_wasted=total_wasted,
        total_items_frozen=total_frozen,
        total_money_saved=round(money_saved, 2),
        total_money_wasted=round(money_wasted, 2),
        total_co2_saved_kg=round(co2_saved, 2),
        meals_enabled=total_saved,
        save_rate_percent=round(save_rate, 1),
        weekly_trend=weekly_trend,
        category_breakdown=dict(cat_breakdown),
    )
