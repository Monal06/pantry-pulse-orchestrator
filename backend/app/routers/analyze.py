from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Body

from app.models.inventory import PantryItemCreate, SpoilageReport, StorageLocation
from app.services import gemini_service, barcode_service, inventory_service, receipt_fallback_service
from app.routers.meals import _meal_history

router = APIRouter(prefix="/analyze", tags=["analyze"])

DEFAULT_USER = "demo-user"


@router.post("/fridge-photo")
async def analyze_fridge_photo(
    photo: UploadFile = File(...),
    user_id: str = Query(default=DEFAULT_USER),
    auto_add: bool = Query(default=True, description="Automatically add detected items to inventory"),
):
    """Analyze a photo of a fridge or cupboard. Identifies items and checks for spoilage."""
    if not photo.content_type or not photo.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_bytes = await photo.read()
    result = await gemini_service.analyze_fridge_photo(image_bytes, photo.content_type)

    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])

    items_created = []
    if auto_add and "items" in result:
        for raw_item in result["items"]:
            item = PantryItemCreate(
                name=raw_item.get("name", "Unknown"),
                category=raw_item.get("category", "other"),
                quantity=raw_item.get("quantity", 1),
                unit=raw_item.get("unit", "item"),
                storage=StorageLocation(raw_item.get("storage", "fridge")),
                is_perishable=raw_item.get("is_perishable", True),
                added_date=date.today(),
            )
            created = await inventory_service.add_item(user_id, item)
            items_created.append(created.model_dump(mode="json"))

    spoilage_reports = result.get("spoilage_reports", [])

    return {
        "items_detected": len(result.get("items", [])),
        "items_added": items_created,
        "spoilage_reports": spoilage_reports,
        "description": result.get("description", ""),
    }


@router.post("/receipt")
async def analyze_receipt(
    photo: UploadFile = File(...),
    user_id: str = Query(default=DEFAULT_USER),
    storage: StorageLocation = Query(default=StorageLocation.FRIDGE),
    auto_add: bool = Query(default=True),
):
    """Analyze a receipt photo to extract purchased food items."""
    if not photo.content_type or not photo.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_bytes = await photo.read()

    # Try Gemini first, then fall back to OCR parsing if Gemini errors.
    used_fallback = False
    try:
        result = await gemini_service.analyze_receipt_photo(image_bytes, photo.content_type)
    except Exception:
        result = {"error": "Primary model failed"}

    if "error" in result:
        used_fallback = True
        result = await receipt_fallback_service.analyze_receipt_photo(image_bytes, photo.content_type)

    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])

    items_created = []
    if auto_add and "items" in result:
        receipt_date = result.get("date", "")
        try:
            if receipt_date:
                item_added_date = datetime.strptime(receipt_date, "%Y-%m-%d").date()
            else:
                item_added_date = date.today()
        except (ValueError, TypeError):
            item_added_date = date.today()

        for raw_item in result["items"]:
            item = PantryItemCreate(
                name=raw_item.get("name", "Unknown"),
                category=raw_item.get("category", "other"),
                quantity=raw_item.get("quantity", 1),
                unit=raw_item.get("unit", "item"),
                storage=storage,
                is_perishable=raw_item.get("is_perishable", True),
                added_date=item_added_date,
            )
            created = await inventory_service.add_item(user_id, item)
            items_created.append(created.model_dump(mode="json"))

    return {
        "items_detected": len(result.get("items", [])),
        "parsed_items": result.get("items", []),
        "items_added": items_created,
        "store_name": result.get("store_name", ""),
        "receipt_date": result.get("date", ""),
        "description": result.get("description", ""),
        "fallback_used": used_fallback,
    }


@router.post("/barcode")
async def analyze_barcode(
    barcode: str = Query(..., description="Barcode string (EAN/UPC)"),
    user_id: str = Query(default=DEFAULT_USER),
    storage: StorageLocation = Query(default=StorageLocation.FRIDGE),
    auto_add: bool = Query(default=True),
):
    """Look up a food item by barcode using the Open Food Facts database."""
    product = await barcode_service.lookup_barcode(barcode)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail=f"Barcode {barcode} not found in Open Food Facts. Try adding the item manually.",
        )

    created_item = None
    if auto_add:
        item = PantryItemCreate(
            name=product["name"],
            category=product["category"],
            quantity=product["quantity"],
            unit=product["unit"],
            storage=storage,
            is_perishable=product["is_perishable"],
            barcode=barcode,
            added_date=date.today(),
        )
        created_item = await inventory_service.add_item(user_id, item)

    return {
        "product": product,
        "item_added": created_item.model_dump(mode="json") if created_item else None,
    }


@router.post("/spoilage-check")
async def check_spoilage(
    photo: UploadFile = File(...),
    item_name: str = Query(..., description="Name of the food item being checked"),
):
    """Check a photo of a specific food item for visual signs of spoilage."""
    if not photo.content_type or not photo.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_bytes = await photo.read()
    result = await gemini_service.check_spoilage(image_bytes, item_name, photo.content_type)

    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])

    return result


@router.post("/voice")
async def analyze_voice_input(
    text: str = Body(..., embed=True, description="Transcribed speech text"),
    user_id: str = Query(default=DEFAULT_USER),
    storage: StorageLocation = Query(default=StorageLocation.FRIDGE),
    auto_add: bool = Query(default=True),
):
    """Parse natural language voice input into food items and add to inventory."""
    result = await gemini_service.parse_voice_input(text)

    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])

    items_created = []
    if auto_add and "items" in result:
        for raw_item in result["items"]:
            item = PantryItemCreate(
                name=raw_item.get("name", "Unknown"),
                category=raw_item.get("category", "other"),
                quantity=raw_item.get("quantity", 1),
                unit=raw_item.get("unit", "item"),
                storage=StorageLocation(raw_item.get("storage", storage.value)),
                is_perishable=raw_item.get("is_perishable", True),
                added_date=date.today(),
            )
            created = await inventory_service.add_item(user_id, item)
            items_created.append(created.model_dump(mode="json"))

    return {
        "parsed_items": result.get("items", []),
        "items_added": items_created,
        "unrecognized": result.get("unrecognized", []),
    }


@router.get("/nutritional-balance")
async def get_nutritional_balance(user_id: str = Query(default=DEFAULT_USER)):
    """Analyze the nutritional balance of current inventory and recent meals."""
    items = await inventory_service.get_all_items(user_id)
    if not items:
        raise HTTPException(status_code=404, detail="Add items to your pantry first.")

    inventory_dicts = [item.model_dump(mode="json") for item in items]
    meals = _meal_history.get(user_id, [])

    result = await gemini_service.analyze_nutritional_balance(inventory_dicts, meals)

    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])

    return result
