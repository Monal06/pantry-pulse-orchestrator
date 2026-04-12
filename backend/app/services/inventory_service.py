from __future__ import annotations

import logging
from datetime import date
from uuid import uuid4

from app.models.inventory import (
    PantryItem,
    PantryItemCreate,
    PantryItemUpdate,
    compute_freshness,
    freshness_category,
)

logger = logging.getLogger(__name__)

# In-memory store keyed by user_id -> list[dict]
# Replace with Supabase calls once connected
_store: dict[str, list[dict]] = {}


def _user_items(user_id: str) -> list[dict]:
    return _store.setdefault(user_id, [])


async def add_item(user_id: str, item: PantryItemCreate) -> PantryItem:
    row = {
        "id": str(uuid4()),
        "user_id": user_id,
        **item.model_dump(mode="json"),
    }
    _user_items(user_id).append(row)
    return PantryItem.from_db_row(row)


async def add_items_bulk(user_id: str, items: list[PantryItemCreate]) -> list[PantryItem]:
    return [await add_item(user_id, item) for item in items]


async def get_all_items(user_id: str) -> list[PantryItem]:
    rows = _user_items(user_id)
    pantry = [PantryItem.from_db_row(r) for r in rows]
    pantry.sort(key=lambda p: p.freshness_score)
    return pantry


async def get_item(user_id: str, item_id: str) -> PantryItem | None:
    for row in _user_items(user_id):
        if row["id"] == item_id:
            return PantryItem.from_db_row(row)
    return None


async def update_item(user_id: str, item_id: str, updates: PantryItemUpdate) -> PantryItem | None:
    for row in _user_items(user_id):
        if row["id"] == item_id:
            for key, val in updates.model_dump(exclude_none=True).items():
                row[key] = val if not hasattr(val, "value") else val.value
            return PantryItem.from_db_row(row)
    return None


async def delete_item(user_id: str, item_id: str) -> bool:
    items = _user_items(user_id)
    for i, row in enumerate(items):
        if row["id"] == item_id:
            items.pop(i)
            return True
    return False


async def use_item(user_id: str, item_id: str, quantity_used: float) -> PantryItem | None:
    """Reduce quantity of an item (e.g. used in a meal). Remove if fully consumed."""
    for i, row in enumerate(_user_items(user_id)):
        if row["id"] == item_id:
            row["quantity"] = max(0, row["quantity"] - quantity_used)
            if row["quantity"] <= 0:
                _user_items(user_id).pop(i)
                return None
            return PantryItem.from_db_row(row)
    return None


async def get_items_by_freshness_tier(user_id: str) -> dict[str, list[PantryItem]]:
    """Group items by freshness category for meal planning and alerts."""
    all_items = await get_all_items(user_id)
    tiers: dict[str, list[PantryItem]] = {"good": [], "use_soon": [], "critical": []}
    for item in all_items:
        tiers[item.freshness_status.value].append(item)
    return tiers


# Track consumed items for shopping list intelligence
_consumption_log: dict[str, list[dict]] = {}


async def log_consumption(user_id: str, item_name: str, category: str) -> None:
    _consumption_log.setdefault(user_id, []).append({
        "name": item_name,
        "category": category,
        "date": str(date.today()),
    })


async def get_consumption_history(user_id: str) -> list[dict]:
    return _consumption_log.get(user_id, [])


# Known non-food noise words and store names that get OCR'd into receipts.
_NOISE_WORDS = {
    "canterbury", "woolworths", "coles", "aldi", "iga", "tesco", "walmart",
    "target", "costco", "kroger", "safeway", "lidl", "waitrose", "asda",
    "loyalty", "receipt", "total", "subtotal", "tax", "change", "cash",
}


async def cleanup_items(user_id: str) -> tuple[int, int]:
    """Remove obvious non-food noise rows and deduplicate exact matches.
    Returns (noise_removed, duplicates_removed)."""
    items = _user_items(user_id)

    # Pass 1: remove noise
    noise_removed = 0
    filtered: list[dict] = []
    for row in items:
        name_lower = row.get("name", "").strip().lower()
        tokens = set(name_lower.split())
        if tokens & _NOISE_WORDS or name_lower in _NOISE_WORDS:
            noise_removed += 1
        else:
            filtered.append(row)

    # Pass 2: deduplicate (same name + category + storage → keep first)
    dupes_removed = 0
    seen: set[str] = set()
    deduped: list[dict] = []
    for row in filtered:
        key = f"{row.get('name','').strip().lower()}|{row.get('category','other')}|{row.get('storage','fridge')}"
        if key in seen:
            dupes_removed += 1
        else:
            seen.add(key)
            deduped.append(row)

    _store[user_id] = deduped
    return noise_removed, dupes_removed
