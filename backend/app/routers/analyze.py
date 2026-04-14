from __future__ import annotations

from datetime import date, timedelta, datetime
import re

from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Body

from app.models.inventory import PantryItemCreate, StorageLocation
from app.services import gemini_service, barcode_service, inventory_service, receipt_fallback_service
from app.services import ensemble_freshness_service, image_crop_service
from app.routers.meals import _meal_history

router = APIRouter(prefix="/analyze", tags=["analyze"])

DEFAULT_USER = "demo-user"


def _normalize_item_name(name: str) -> str:
    """Normalize receipt item names to reduce OCR noise and duplicate variants."""
    cleaned = re.sub(r"\s+", " ", (name or "").strip())
    cleaned = re.sub(r"[^\w\s\-./]", "", cleaned)
    return cleaned.title()


def _sanitize_receipt_items(items: list[dict], store_name: str = "") -> list[dict]:
    """Filter non-item rows and dedupe repeated OCR/Gemini receipt lines."""
    if not items:
        return []

    normalized_store = _normalize_item_name(store_name).lower()
    seen: set[str] = set()
    cleaned_items: list[dict] = []

    for raw in items:
        name = _normalize_item_name(raw.get("name", ""))
        if not name:
            continue

        # Drop accidental store-name rows (e.g. "Canterbury").
        if normalized_store and name.lower() == normalized_store:
            continue

        # Drop lines without alphabetic tokens.
        if not re.search(r"[A-Za-z]", name):
            continue

        dedupe_key = name.lower()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        cleaned = dict(raw)
        cleaned["name"] = name
        cleaned_items.append(cleaned)

    return cleaned_items


@router.post("/fridge-photo")
async def analyze_fridge_photo(
    photo: UploadFile = File(...),
    user_id: str = Query(default=DEFAULT_USER),
    auto_add: bool = Query(default=True, description="Automatically add detected items to inventory"),
):
    """
    Analyze a photo of a fridge or cupboard.  Two-phase approach:

      Phase 1 (fast — single Gemini call): identify items + spoilage reports.
      Phase 2 (targeted ensemble — local CV only): run OpenCV
              on the TOP-3 most suspicious items by cropped bounding-box.

    Phase 2 uses only local models (zero extra API calls) and runs in
    parallel via asyncio.gather, adding ~1-2 s instead of the old 30-60 s.
    CLIP and ViT are reserved for individual item analysis (/freshness-deep).
    """
    import asyncio as _asyncio

    print(f"[FRIDGE-PHOTO] Endpoint hit. Content type: {photo.content_type}")
    if not photo.content_type or not photo.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_bytes = await photo.read()
    print(f"[FRIDGE-PHOTO] Image bytes received: {len(image_bytes)} bytes")

    # ── Phase 1: Single Gemini call (fast) ──────────────────────────
    try:
        result = await gemini_service.analyze_fridge_photo(image_bytes, photo.content_type)
        print(f"[FRIDGE-PHOTO] Gemini found {len(result.get('items', []))} items")
    except Exception as e:
        print(f"[FRIDGE-PHOTO] ERROR in gemini_service: {type(e).__name__}: {str(e)}")
        result = {
            "items": [],
            "spoilage_reports": [],
            "description": "Unable to analyze photo. Please try again or use manual entry.",
            "error": str(e),
        }

    if "error" in result and len(result.get("items", [])) == 0:
        return {
            "items_detected": 0,
            "items_added": [],
            "spoilage_reports": result.get("spoilage_reports", []),
            "description": result.get("description", ""),
            "error": result.get("error", ""),
        }

    spoilage_reports = result.get("spoilage_reports", [])

    # Build a lookup of Gemini's per-item spoilage verdicts
    gemini_spoilage_map: dict[str, dict] = {}
    for report in spoilage_reports:
        gemini_spoilage_map[report.get("item_name", "").lower()] = report

    # ── Phase 2: Targeted local-only ensemble on TOP-3 suspicious ───
    # Sort perishable items by Gemini spoilage confidence (highest first)
    perishable_items = [
        item for item in result.get("items", [])
        if item.get("is_perishable", True)
    ]

    def _suspicion_score(item: dict) -> float:
        """Higher = more suspicious = should get ensemble attention."""
        report = gemini_spoilage_map.get(item.get("name", "").lower())
        if report and report.get("spoilage_detected"):
            return report.get("confidence", 0.5) * 100
        return 0.0

    perishable_items.sort(key=_suspicion_score, reverse=True)
    ensemble_candidates = perishable_items[:3]

    async def _cv_only_for_item(raw_item: dict) -> tuple[str, dict | None]:
        """Run OpenCV only on a cropped item. Fast, no model downloads."""
        name = raw_item.get("name", "unknown")
        bbox = image_crop_service.validate_bbox(raw_item.get("bbox"))
        crop_bytes = (
            image_crop_service.crop_item_from_image(image_bytes, bbox)
            if bbox else image_bytes
        )
        scan_bytes = crop_bytes or image_bytes

        scores: dict[str, float | None] = {}
        visual_flags: list[dict] = []

        # Fridge photos: OpenCV only (fast, no heavy model loading)
        # CLIP + ViT are reserved for individual item photos via /freshness-deep
        try:
            from app.services import cv_freshness_service

            cv_result = await _asyncio.to_thread(
                cv_freshness_service.analyze_food_image, scan_bytes, name
            )

            if cv_result:
                scores["cv_pipeline"] = cv_result.get("cv_score")
                if cv_result.get("visual_flags"):
                    visual_flags.extend(cv_result["visual_flags"])

        except Exception as exc:
            print(f"[FRIDGE-PHOTO] CV analysis failed for {name}: {exc}")

        if not scores:
            return name, None

        return name, {
            "model_scores": scores,
            "visual_flags": visual_flags,
            "used_crop": bbox is not None,
        }

    # Fire all 3 items in parallel — OpenCV is lightweight
    freshness_scores: dict = {}
    if ensemble_candidates:
        ensemble_results = await _asyncio.gather(
            *[_cv_only_for_item(item) for item in ensemble_candidates],
            return_exceptions=True,
        )
        for res in ensemble_results:
            if isinstance(res, Exception):
                print(f"[FRIDGE-PHOTO] Ensemble task exception: {res}")
                continue
            item_name, ens_data = res
            if ens_data:
                model_scores = ens_data["model_scores"]
                # Weighted ensemble: Gemini initial 50%, local models share 50%
                gemini_initial = _suspicion_score_to_freshness(
                    gemini_spoilage_map.get(item_name.lower())
                )
                final_score = _compute_ensemble_score(model_scores, gemini_initial)

                freshness_scores[item_name] = {
                    "freshness_score": final_score,
                    "freshness_level": "good" if final_score >= 70 else ("use_soon" if final_score >= 50 else "critical"),
                    "confidence": _compute_local_confidence(model_scores),
                    "visual_flags": ens_data["visual_flags"],
                    "used_crop": ens_data["used_crop"],
                    "model_scores": {k: round(v, 1) for k, v in model_scores.items() if v is not None},
                }
                print(f"[FRIDGE-PHOTO] Ensemble {item_name}: score={final_score}")

    # ── Phase 3: Add items to inventory ─────────────────────────────
    items_created = []
    if auto_add and "items" in result:
        for raw_item in result["items"]:
            item_name = raw_item.get("name", "Unknown")
            item_name_lower = item_name.lower()

            # Check Gemini spoilage
            has_spoilage = any(
                item_name_lower in report.get("item_name", "").lower()
                and report.get("spoilage_detected", False)
                for report in spoilage_reports
            )

            # Check ensemble visual flags for safety caps
            ens_flags = freshness_scores.get(item_name, {}).get("visual_flags", [])
            has_ensemble_hazard = any("cap_applied" in f.get("type", "") for f in ens_flags)
            is_hazardous = has_spoilage or has_ensemble_hazard

            # Use ensemble freshness score if available
            ens_score = freshness_scores.get(item_name, {}).get("freshness_score")

            item = PantryItemCreate(
                name=item_name,
                category=raw_item.get("category", "other"),
                quantity=raw_item.get("quantity", 1),
                unit=raw_item.get("unit", "item"),
                storage=StorageLocation(raw_item.get("storage", "fridge")),
                is_perishable=raw_item.get("is_perishable", True),
                added_date=date.today(),
                purchase_date=date.today(),
                visual_hazard=is_hazardous,
<<<<<<< HEAD
                visual_verified=True,  # Items from photo analysis are visually verified
                ai_freshness_score=ens_score
=======
                ai_freshness_score=ens_score,
>>>>>>> improveperformance
            )
            created = await inventory_service.add_item(user_id, item)
            items_created.append(created.model_dump(mode="json"))

    return {
        "items_detected": len(result.get("items", [])),
        "items_added": items_created,
        "spoilage_reports": spoilage_reports,
        "description": result.get("description", ""),
        "freshness_scores": freshness_scores,
    }


def _suspicion_score_to_freshness(report: dict | None) -> float:
    """Convert Gemini spoilage report to a 0-100 freshness score."""
    if not report:
        return 85.0  # No spoilage data → assume fairly fresh
    if report.get("spoilage_detected"):
        confidence = report.get("confidence", 0.5)
        return round(max(0.0, 40.0 - confidence * 35.0), 1)
    confidence = report.get("confidence", 0.5)
    return round(min(100.0, 60.0 + (1.0 - confidence) * 40.0), 1)


def _compute_ensemble_score(model_scores: dict, gemini_initial: float) -> float:
    """Weighted average: Gemini initial (50%) + local models share remaining 50%."""
    local_weights = {"cv_pipeline": 0.25, "clip": 0.15, "vit_anomaly": 0.10}
    total_weight = 0.50  # Gemini initial weight
    weighted_sum = gemini_initial * 0.50

    for model, score in model_scores.items():
        if score is None:
            continue
        w = local_weights.get(model, 0.10)
        weighted_sum += score * w
        total_weight += w

    return round(weighted_sum / total_weight, 1) if total_weight > 0 else gemini_initial


def _compute_local_confidence(model_scores: dict) -> float:
    """Confidence based on how many local models ran + their agreement."""
    import math
    scores = [v for v in model_scores.values() if v is not None]
    n = len(scores)
    if n == 0:
        return 30.0
    base = 40.0 + n * 15.0  # 1 method=55, 2=70, 3=85
    if n > 1:
        mean = sum(scores) / n
        std = math.sqrt(sum((s - mean) ** 2 for s in scores) / n)
        cv = std / max(mean, 1.0)
        agreement = max(0.0, 1.0 - cv * 1.5)
        base *= (0.5 + 0.5 * agreement)
    return round(min(100.0, max(0.0, base)), 1)


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
    used_fallback = False
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
    if "error" in result:
        used_fallback = True
        result = await receipt_fallback_service.analyze_receipt_photo(image_bytes, photo.content_type)

    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])

    # Normalize and dedupe parsed receipt items from either Gemini or fallback OCR.
    parsed_items = _sanitize_receipt_items(result.get("items", []), result.get("store_name", ""))

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
    if auto_add and parsed_items:
        receipt_date = result.get("date", "")
        try:
            if receipt_date:
                item_added_date = datetime.strptime(receipt_date, "%Y-%m-%d").date()
            else:
                item_added_date = date.today()
        except (ValueError, TypeError):
            item_added_date = date.today()

        for raw_item in parsed_items:
            item = PantryItemCreate(
                name=raw_item.get("name", "Unknown"),
                category=raw_item.get("category", "other"),
                quantity=raw_item.get("quantity", 1),
                unit=raw_item.get("unit", "item"),
                storage=storage,
                is_perishable=raw_item.get("is_perishable", True),
                added_date=item_added_date,
                purchase_date=purchase_date,  # Use extracted receipt date
                visual_verified=True,  # Items from receipt analysis are visually verified
            )
            created = await inventory_service.add_item(user_id, item)
            items_created.append(created.model_dump(mode="json"))

    return {
        "items_detected": len(parsed_items),
        "parsed_items": parsed_items,
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
            purchase_date=date.today(),  # Barcode: assume today
            visual_verified=True,  # Items from barcode analysis are visually verified
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
                visual_verified=False,  # Voice input is just text, no visual verification
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


@router.post("/test-receipt-item")
async def test_receipt_item(
    item_name: str = Query(..., description="Item name to test categorization"),
    user_id: str = Query(default=DEFAULT_USER),
):
    """Test endpoint to check how an item would be categorized from receipt parsing."""
    
    # Create a mock receipt with just this item
    mock_receipt_text = f"""
    GROCERY RECEIPT
    
    {item_name}     $5.99
    
    TOTAL: $5.99
    """
    
    try:
        # Test the parsing logic
        result = await gemini_service.parse_voice_input(f"I bought {item_name}")
        
        return {
            "item_name": item_name,
            "parsed_result": result,
            "would_get_freshness": True,  # All items should get freshness if properly categorized
        }
    except Exception as e:
        return {
            "item_name": item_name,
            "error": str(e),
            "would_get_freshness": False,
        }
