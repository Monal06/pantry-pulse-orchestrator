from __future__ import annotations

import logging
from datetime import date

from app.services import inventory_service

logger = logging.getLogger(__name__)

_notification_log: dict[str, list[dict]] = {}


async def check_freshness_alerts(user_id: str) -> list[dict]:
    """Check inventory for items that crossed freshness thresholds and generate alerts."""
    items = await inventory_service.get_all_items(user_id)
    alerts: list[dict] = []

    critical = [i for i in items if i.freshness_score < 50 and i.is_perishable]
    use_soon = [i for i in items if 50 <= i.freshness_score < 70 and i.is_perishable]
    freezable = [
        i for i in items
        if i.is_perishable and i.storage.value != "freezer" and 30 <= i.freshness_score < 70
    ]

    if critical:
        names = ", ".join(i.name for i in critical[:5])
        suffix = f" and {len(critical) - 5} more" if len(critical) > 5 else ""
        alerts.append({
            "type": "critical",
            "title": "Items need urgent attention!",
            "body": f"{names}{suffix} — use them now or they'll go to waste.",
            "count": len(critical),
        })

    if use_soon:
        names = ", ".join(i.name for i in use_soon[:5])
        suffix = f" and {len(use_soon) - 5} more" if len(use_soon) > 5 else ""
        alerts.append({
            "type": "use_soon",
            "title": "Items expiring soon",
            "body": f"{names}{suffix} — plan to use these in your next meals.",
            "count": len(use_soon),
        })

    if freezable:
        names = ", ".join(i.name for i in freezable[:3])
        alerts.append({
            "type": "freeze_suggestion",
            "title": "Consider freezing",
            "body": f"{names} could be frozen to extend their freshness.",
            "count": len(freezable),
        })

    _notification_log.setdefault(user_id, []).extend(
        [{**a, "date": str(date.today())} for a in alerts]
    )

    return alerts


async def get_notification_history(user_id: str) -> list[dict]:
    return _notification_log.get(user_id, [])
