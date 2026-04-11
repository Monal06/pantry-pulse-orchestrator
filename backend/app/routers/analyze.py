from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Body

from app.models.inventory import PantryItemCreate, SpoilageReport, StorageLocation
from app.services import gemini_service, barcode_service, inventory_service
from app.services import ensemble_freshness_service, image_crop_service
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
    print(f"[FRIDGE-PHOTO] Endpoint hit. Content type: {photo.content_type}")
    if not photo.content_type or not photo.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_bytes = await photo.read()
    print(f"[FRIDGE-PHOTO] Image bytes received: {len(image_bytes)} bytes")
    try:
        result = await gemini_service.analyze_fridge_photo(image_bytes, photo.content_type)
        print(f"[FRIDGE-PHOTO] Gemini result: {result}")
    except Exception as e:
        print(f"[FRIDGE-PHOTO] ERROR in gemini_service: {type(e).__name__}: {str(e)}")
        # Return fallback data instead of crashing
        result = {
            "items": [],
            "spoilage_reports": [],
            "description": "Unable to analyze photo. Please try again or use manual entry.",
            "error": str(e)
        }

    if "error" in result and len(result.get("items", [])) == 0:
        # If there's an error and no items, it's a real failure
        # But we still return some fallback rather than 502
        return {
            "items_detected": 0,
            "items_added": [],
            "spoilage_reports": result.get("spoilage_reports", []),
            "description": result.get("description", ""),
            "error": result.get("error", ""),
        }

    items_created = []
    spoilage_reports = result.get("spoilage_reports", [])

    # ------------------------------------------------------------------
    # Module B: Per-item ensemble freshness on cropped regions.
    # Gemini returns a bbox [x1,y1,x2,y2] (normalised 0-1) for each item.
    # We crop that region and run the full ensemble on the close-up crop.
    # Capped at 6 items concurrently to avoid overloading the CPU.
    # Items without a valid bbox fall back to Gemini-only scoring.
    # All existing keys are unaffected — freshness_scores is a NEW key.
    # ------------------------------------------------------------------
    perishable_items = [
        item for item in result.get("items", [])
        if item.get("is_perishable", True)
    ]

    async def _ensemble_for_item(raw_item: dict) -> tuple[str, dict | None, dict]:
        """Crop + ensemble for one item. Returns (item_name, result_or_None, raw_item)."""
        name = raw_item.get("name", "unknown")
        bbox = image_crop_service.validate_bbox(raw_item.get("bbox"))
        crop_bytes = (
            image_crop_service.crop_item_from_image(image_bytes, bbox)
            if bbox else None
        )
        # Fall back to full image if no bbox
        scan_bytes = crop_bytes or image_bytes
        try:
            res = await ensemble_freshness_service.run_ensemble_analysis(
                image_bytes=scan_bytes,
                food_name=name,
                food_category=raw_item.get("category", "other"),
                storage=raw_item.get("storage", "fridge"),
                added_date=date.today(),
                mime_type=photo.content_type or "image/jpeg",
            )
            return name, res, raw_item
        except Exception as exc:
            print(f"[FRIDGE-PHOTO] Ensemble failed for {name}: {exc}")
            return name, None, raw_item

    # Run ensemble on up to 6 perishable items concurrently
    MAX_ENSEMBLE_ITEMS = 6
    freshness_scores: dict = {}
    if perishable_items:
        import asyncio as _asyncio
        sem = _asyncio.Semaphore(3)  # max 3 parallel ensemble runs

        async def _guarded(item):
            async with sem:
                return await _ensemble_for_item(item)

        tasks = [_guarded(item) for item in perishable_items[:MAX_ENSEMBLE_ITEMS]]
        ensemble_results = await _asyncio.gather(*tasks, return_exceptions=False)

        for item_name, ens_result, _raw in ensemble_results:
            if ens_result:
                freshness_scores[item_name] = {
                    "freshness_score":  ens_result.get("freshness_score"),
                    "freshness_level":  ens_result.get("freshness_level"),
                    "confidence":       ens_result.get("confidence"),
                    "visual_flags":     ens_result.get("visual_flags", []),
                    "days_remaining":   ens_result.get("bayesian_prediction", {}).get("predicted_days_remaining"),
                    "llm_reasoning":    ens_result.get("llm_reasoning"),
                    "used_crop":        _raw.get("bbox") is not None,
                }
                print(f"[FRIDGE-PHOTO] Ensemble {item_name}: score={ens_result.get('freshness_score')}")

    if auto_add and "items" in result:
        for raw_item in result["items"]:
            item_name = raw_item.get("name", "Unknown")
            item_name_lower = item_name.lower()

            # Check if this item name appears in any spoilage report
            # Use substring matching to handle suffixes like "(left)", "(right)"
            has_spoilage = any(
                item_name_lower in report.get("item_name", "").lower() and
                report.get("spoilage_detected", False)
                for report in spoilage_reports
            )

            # If item has visual spoilage, set purchase_date to 10 days ago
            # This makes freshness_score < 50, triggering Exit Strategy
            purchase_date = (date.today() - timedelta(days=10)) if has_spoilage else date.today()

            item = PantryItemCreate(
                name=item_name,
                category=raw_item.get("category", "other"),
                quantity=raw_item.get("quantity", 1),
                unit=raw_item.get("unit", "item"),
                storage=StorageLocation(raw_item.get("storage", "fridge")),
                is_perishable=raw_item.get("is_perishable", True),
                added_date=date.today(),
                purchase_date=purchase_date,
            )
            created = await inventory_service.add_item(user_id, item)
            items_created.append(created.model_dump(mode="json"))

    return {
        "items_detected": len(result.get("items", [])),
        "items_added": items_created,
        "spoilage_reports": spoilage_reports,
        "description": result.get("description", ""),
        # Per-item ensemble freshness scores (new key — safe to ignore if not needed)
        "freshness_scores": freshness_scores,
    }


@router.post("/receipt")
async def analyze_receipt(
    photo: UploadFile = File(...),
    user_id: str = Query(default=DEFAULT_USER),
    storage: StorageLocation = Query(default=StorageLocation.FRIDGE),
    auto_add: bool = Query(default=True),
):
    """Analyze a receipt photo to extract purchased food items.

    Automatically extracts receipt date and uses it as purchase_date for items,
    enabling accurate age verification even if items are added to system later.
    """
    if not photo.content_type or not photo.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_bytes = await photo.read()
    try:
        result = await gemini_service.analyze_receipt_photo(image_bytes, photo.content_type)
    except Exception as e:
        print(f"[RECEIPT] ERROR in gemini_service: {type(e).__name__}: {str(e)}")
        result = {
            "items": [],
            "date": "",
            "store_name": "",
            "description": "Unable to analyze receipt. Please try again or use manual entry.",
            "error": str(e)
        }

    if "error" in result and len(result.get("items", [])) == 0:
        return {
            "items_detected": 0,
            "items_added": [],
            "store_name": result.get("store_name", ""),
            "receipt_date": result.get("date", ""),
            "description": result.get("description", ""),
            "error": result.get("error", ""),
        }

    # Extract receipt date for accurate purchase_date
    receipt_date_str = result.get("date", "")
    purchase_date = None
    if receipt_date_str:
        try:
            purchase_date = date.fromisoformat(receipt_date_str)
        except (ValueError, TypeError):
            # If date parsing fails, let it default to None (will use added_date)
            pass

    items_created = []
    if auto_add and "items" in result:
        for raw_item in result["items"]:
            item = PantryItemCreate(
                name=raw_item.get("name", "Unknown"),
                category=raw_item.get("category", "other"),
                quantity=raw_item.get("quantity", 1),
                unit=raw_item.get("unit", "item"),
                storage=storage,
                is_perishable=raw_item.get("is_perishable", True),
                added_date=date.today(),
                purchase_date=purchase_date,  # Use extracted receipt date
            )
            created = await inventory_service.add_item(user_id, item)
            items_created.append(created.model_dump(mode="json"))

    return {
        "items_detected": len(result.get("items", [])),
        "items_added": items_created,
        "store_name": result.get("store_name", ""),
        "receipt_date": result.get("date", ""),
        "description": result.get("description", ""),
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
            purchase_date=date.today(),  # Barcode: assume today
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
    try:
        result = await gemini_service.check_spoilage(image_bytes, item_name, photo.content_type)
    except Exception as e:
        print(f"[SPOILAGE-CHECK] ERROR in gemini_service: {type(e).__name__}: {str(e)}")
        result = {
            "item_name": item_name,
            "spoilage_detected": False,
            "confidence": 0.0,
            "error": str(e)
        }

    return result


@router.post("/voice")
async def analyze_voice_input(
    text: str = Body(..., embed=True, description="Transcribed speech text"),
    user_id: str = Query(default=DEFAULT_USER),
    storage: StorageLocation = Query(default=StorageLocation.FRIDGE),
    auto_add: bool = Query(default=True),
):
    """Parse natural language voice input into food items and add to inventory."""
    print(f"[VOICE] Endpoint hit. Text: {text}")
    try:
        result = await gemini_service.parse_voice_input(text)
        print(f"[VOICE] Gemini result: {result}")
    except Exception as e:
        print(f"[VOICE] ERROR in gemini_service: {type(e).__name__}: {str(e)}")
        result = {
            "items": [],
            "unrecognized": [],
            "error": str(e)
        }

    if "error" in result and len(result.get("items", [])) == 0:
        return {
            "parsed_items": [],
            "items_added": [],
            "unrecognized": result.get("unrecognized", []),
            "error": result.get("error", ""),
        }

    items_created = []
    if auto_add and "items" in result:
        for raw_item in result["items"]:
            # Use the LLM-extracted purchase_date if available, otherwise default to today
            raw_purchase = raw_item.get("purchase_date")
            try:
                parsed_purchase = date.fromisoformat(raw_purchase) if raw_purchase else date.today()
            except (ValueError, TypeError):
                parsed_purchase = date.today()

            item = PantryItemCreate(
                name=raw_item.get("name", "Unknown"),
                category=raw_item.get("category", "other"),
                quantity=raw_item.get("quantity", 1),
                unit=raw_item.get("unit", "item"),
                storage=StorageLocation(raw_item.get("storage", storage.value)),
                is_perishable=raw_item.get("is_perishable", True),
                added_date=date.today(),
                purchase_date=parsed_purchase,
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

    try:
        result = await gemini_service.analyze_nutritional_balance(inventory_dicts, meals)
    except Exception as e:
        print(f"[NUTRITIONAL-BALANCE] ERROR in gemini_service: {type(e).__name__}: {str(e)}")
        result = {
            "balance": "unable_to_analyze",
            "recommendations": ["Try again later or manually review your pantry"],
            "error": str(e)
        }

    return result


# ---------------------------------------------------------------------------
# Deep Ensemble Freshness Analysis
# ---------------------------------------------------------------------------

@router.post("/freshness-deep")
async def analyze_freshness_deep(
    photo: UploadFile = File(...),
    item_name: str = Query(default="unknown food item", description="Name of the food item"),
    category: str = Query(default="other", description="Food category (dairy, meat, fruit, etc.)"),
    storage: str = Query(default="fridge", description="Storage location: fridge/freezer/pantry/counter"),
    purchase_date: str = Query(default="", description="Purchase date ISO string YYYY-MM-DD (optional)"),
):
    """
    Deep multi-method freshness analysis using a 4-signal ensemble.

    Combines four independent AI/CV methods:

    1. **Gemini Visual Assessment** (40% weight) — LLM multimodal spoilage detection
    2. **CV Pipeline** (25% weight) — OpenCV colour space analysis (HSV+LAB), mold masks,
       texture quality (Laplacian variance), context-aware for yellow/dark foods
    3. **ViT Anomaly Detection** (20% weight) — google/vit-base-patch16-224 CLS-token
       activation statistics; higher anomaly = more spoiled
    4. **CLIP Zero-Shot** (15% weight) — openai/clip-vit-base-patch32 comparing image
       against "fresh food" vs "moldy food" text prompts

    Plus:
    - **Bayesian Decay Model** — combines the ensemble score with the time-based prior
      (existing linear decay formula) via Gaussian conjugate update
    - **Groq/Llama 3.3 70B Reasoning** — natural-language safety summary
    - **Confidence scoring** — agreement between methods, image quality, method count
    - **Safety hard caps** — mold → score ≤ 25; rot → score ≤ 30

    If ML models (CLIP/ViT) are not installed, they are skipped
    and their weights redistributed to the remaining methods.
    """
    if not photo.content_type or not photo.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_bytes = await photo.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty image file")

    # Parse optional purchase date
    parsed_purchase_date = None
    if purchase_date:
        try:
            from datetime import date as _date
            parsed_purchase_date = _date.fromisoformat(purchase_date)
        except (ValueError, TypeError):
            pass  # Ignore bad date strings — Bayesian prior uses added_date only

    try:
        result = await ensemble_freshness_service.run_ensemble_analysis(
            image_bytes=image_bytes,
            food_name=item_name,
            food_category=category,
            storage=storage,
            added_date=date.today(),
            purchase_date=parsed_purchase_date,
            mime_type=photo.content_type or "image/jpeg",
        )
    except Exception as e:
        print(f"[FRESHNESS-DEEP] Fatal error in ensemble: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ensemble freshness analysis failed: {str(e)}",
        )

    return result
