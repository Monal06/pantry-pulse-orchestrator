from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.models.inventory import (
    PantryItem,
    PantryItemCreate,
    PantryItemUpdate,
    StorageLocation,
)
from app.models.waste import WasteEventType
from app.services import inventory_service, waste_service


class _ReceiptItem(BaseModel):
    name: str
    category: str = "other"
    quantity: float = 1.0
    unit: str = "item"
    is_perishable: bool = True


class _BulkReceiptAdd(BaseModel):
    items: list[_ReceiptItem]
    purchase_date: str = ""
    storage: str = "fridge"

router = APIRouter(prefix="/inventory", tags=["inventory"])

DEFAULT_USER = "demo-user"


@router.get("", response_model=list[PantryItem])
async def list_items(user_id: str = Query(default=DEFAULT_USER)):
    """List all pantry items sorted by freshness (lowest first)."""
    return await inventory_service.get_all_items(user_id)


@router.get("/tiers")
async def get_freshness_tiers(user_id: str = Query(default=DEFAULT_USER)):
    """Get inventory grouped by freshness tier: good, use_soon, critical."""
    tiers = await inventory_service.get_items_by_freshness_tier(user_id)
    return {
        tier: [item.model_dump(mode="json") for item in items]
        for tier, items in tiers.items()
    }


@router.get("/freeze-suggestions")
async def get_freeze_suggestions(user_id: str = Query(default=DEFAULT_USER)):
    """Get items that should be frozen to extend their life (freshness 30-70, not already frozen)."""
    items = await inventory_service.get_all_items(user_id)
    suggestions = [
        item.model_dump(mode="json")
        for item in items
        if item.is_perishable
        and 30 <= item.freshness_score < 70
        and item.storage != StorageLocation.FREEZER
    ]
    return {
        "suggestions": suggestions,
        "message": (
            f"{len(suggestions)} item(s) could be frozen to extend their freshness."
            if suggestions
            else "No items currently need freezing."
        ),
    }


@router.post("", response_model=PantryItem)
async def add_item(item: PantryItemCreate, user_id: str = Query(default=DEFAULT_USER)):
    """Manually add a single item to the pantry."""
    return await inventory_service.add_item(user_id, item)


@router.post("/bulk", response_model=list[PantryItem])
async def add_items_bulk(
    body: _BulkReceiptAdd,
    user_id: str = Query(default=DEFAULT_USER),
):
    """Bulk-add items parsed from a receipt with a confirmed purchase date."""
    try:
        added_date = date.fromisoformat(body.purchase_date) if body.purchase_date else date.today()
        if added_date > date.today():
            added_date = date.today()
    except ValueError:
        added_date = date.today()

    # Requested storage is the default; non-perishable categories override to pantry.
    try:
        default_storage = StorageLocation(body.storage)
    except ValueError:
        default_storage = StorageLocation.FRIDGE

    PANTRY_CATEGORIES = {"canned", "dry_goods", "condiment", "bread"}

    to_create = []
    seen: set[str] = set()
    for item in body.items:
        normalized_name = " ".join(item.name.strip().split()).lower()

        # Auto-correct storage: shelf-stable categories belong in the pantry
        item_storage = (
            StorageLocation.PANTRY
            if item.category in PANTRY_CATEGORIES
            else default_storage
        )

        key = f"{normalized_name}|{item.category}|{item.unit}|{item_storage.value}|{added_date.isoformat()}"
        if key in seen:
            continue
        seen.add(key)

        to_create.append(
            PantryItemCreate(
                name=item.name,
                category=item.category,
                quantity=item.quantity,
                unit=item.unit,
                storage=item_storage,
                is_perishable=item.is_perishable,
                added_date=added_date,
            )
        )

    return await inventory_service.add_items_bulk(user_id, to_create)


@router.post("/cleanup", response_model=dict)
async def cleanup_inventory(user_id: str = Query(default=DEFAULT_USER)):
    """Remove non-food noise items (e.g. store names picked up from receipts) and
    deduplicate existing pantry rows that have the same name, category and storage."""
    removed, deduped = await inventory_service.cleanup_items(user_id)
    return {"removed_noise": removed, "removed_duplicates": deduped, "total_cleaned": removed + deduped}


@router.put("/{item_id}", response_model=PantryItem)
async def update_item(
    item_id: str,
    updates: PantryItemUpdate,
    user_id: str = Query(default=DEFAULT_USER),
):
    result = await inventory_service.update_item(user_id, item_id, updates)
    if result is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return result


@router.delete("/{item_id}")
async def delete_item(
    item_id: str,
    reason: str = Query(default="wasted", description="Reason: wasted or donated"),
    user_id: str = Query(default=DEFAULT_USER),
):
    """Remove an item from inventory. Logs it as wasted or donated for tracking."""
    item = await inventory_service.get_item(user_id, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    deleted = await inventory_service.delete_item(user_id, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")

    event_type = WasteEventType.DONATED if reason == "donated" else WasteEventType.WASTED
    await waste_service.log_event(user_id, item.name, item.category, event_type, item.quantity)

    return {"status": "deleted", "tracked_as": event_type.value}


@router.post("/{item_id}/use")
async def use_item(
    item_id: str,
    quantity: float = Query(gt=0),
    user_id: str = Query(default=DEFAULT_USER),
):
    """Record usage of an item (e.g. used in a meal). Removes if fully consumed."""
    item = await inventory_service.get_item(user_id, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    result = await inventory_service.use_item(user_id, item_id, quantity)
    await inventory_service.log_consumption(user_id, item.name, item.category)
    await waste_service.log_event(user_id, item.name, item.category, WasteEventType.SAVED, quantity)

    if result is None:
        return {"status": "fully consumed", "item": item.name}
    return {"status": "updated", "remaining_quantity": result.quantity}


@router.post("/{item_id}/freeze")
async def freeze_item(
    item_id: str,
    user_id: str = Query(default=DEFAULT_USER),
):
    """Move an item to the freezer to dramatically slow freshness decay."""
    item = await inventory_service.get_item(user_id, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.storage == StorageLocation.FREEZER:
        return {"status": "already_frozen", "item": item.name}

    updates = PantryItemUpdate(storage=StorageLocation.FREEZER)
    updated = await inventory_service.update_item(user_id, item_id, updates)

    await waste_service.log_event(user_id, item.name, item.category, WasteEventType.FROZEN, item.quantity)

    return {
        "status": "frozen",
        "item": updated.name if updated else item.name,
        "new_freshness_score": updated.freshness_score if updated else None,
        "message": f"Moved {item.name} to freezer. Freshness decay is now dramatically slower.",
    }
