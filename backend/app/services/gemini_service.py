from __future__ import annotations

import asyncio
import json
import logging
import random
import itertools
from typing import Any
from datetime import datetime, timedelta

from google import genai
from google.genai import types

from app.config import get_settings
from app.services import receipt_fallback_service

logger = logging.getLogger(__name__)

_client: genai.Client | None = None
_key_iterator: itertools.cycle | None = None
_exhausted_keys: dict[str, datetime] = {}  # Track exhausted keys with timestamp


def _is_quota_error(exc: Exception) -> bool:
    """Return True if the exception is a quota/daily limit error."""
    err = str(exc).lower()
    return any(tok in err for tok in (
        "quota", "daily limit", "exceeded", "quota_exceeded",
        "insufficient quota", "billing", "free tier",
    ))


def _get_next_gemini_key() -> str:
    """Rotate through multiple Gemini API keys, skipping exhausted ones."""
    global _key_iterator, _exhausted_keys
    settings = get_settings()
    keys = settings.get_all_gemini_keys()

    if not keys:
        raise ValueError("No Gemini API keys configured. Set GEMINI_API_KEY or GEMINI_API_KEYS")

    # Clean up exhausted keys that have been waiting for 24 hours (quota resets daily)
    now = datetime.now()
    _exhausted_keys = {
        key: timestamp
        for key, timestamp in _exhausted_keys.items()
        if now - timestamp < timedelta(hours=24)
    }

    # Filter out exhausted keys
    available_keys = [k for k in keys if k not in _exhausted_keys]

    if not available_keys:
        logger.warning(
            f"All {len(keys)} Gemini API keys are exhausted. "
            f"Quota resets in ~{24 - (now.hour)} hours."
        )
        # Return any key anyway - might work if quota just reset
        available_keys = keys

    # If multiple keys, rotate through available ones
    if len(available_keys) > 1:
        if _key_iterator is None or set(_exhausted_keys.keys()):
            # Recreate iterator with only available keys
            _key_iterator = itertools.cycle(available_keys)
        key = next(_key_iterator)
        logger.debug(
            f"Using Gemini key rotation "
            f"(available: {len(available_keys)}/{len(keys)} keys)"
        )
        return key

    # Single available key
    return available_keys[0]


def _mark_key_exhausted(key: str) -> None:
    """Mark a key as exhausted so it's skipped in rotation."""
    global _exhausted_keys
    _exhausted_keys[key] = datetime.now()
    logger.warning(
        f"Gemini API key exhausted (daily quota). "
        f"Total exhausted: {len(_exhausted_keys)}. "
        f"This key will be retried in ~24 hours."
    )


def _get_client() -> genai.Client:
    """Get Gemini client with rotated API key."""
    # Don't cache client - create fresh one with rotated key
    return genai.Client(api_key=_get_next_gemini_key())


def _get_models() -> list[str]:
    """Return the ordered list of models to try."""
    return [m.strip() for m in get_settings().gemini_models.split(",") if m.strip()]


def _is_overload_error(exc: Exception) -> bool:
    """Return True if the exception looks like a transient overload / rate-limit."""
    err = str(exc).lower()
    return any(tok in err for tok in (
        "503", "unavailable", "overloaded", "high demand",
        "resource_exhausted", "429", "rate limit",
    ))


async def _generate_with_retry(contents: list) -> str:
    """Call Gemini with exponential-backoff retry and model fallback.

    For each model in the configured list, retry up to ``gemini_max_retries``
    times with exponential backoff + jitter.  If every attempt on a model
    returns a 503/429/overload error, fall back to the next model.
    """
    models = _get_models()
    max_retries = get_settings().gemini_max_retries
    last_exc: Exception | None = None
    current_key = None

    for model in models:
        for attempt in range(1, max_retries + 1):
            try:
                # Get fresh client with rotated key for each attempt
                client = _get_client()
                current_key = _get_next_gemini_key()  # Track which key we're using

                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                )
                if attempt > 1 or model != models[0]:
                    logger.info(
                        "Gemini succeeded on model=%s attempt=%d", model, attempt,
                    )
                return response.text
            except Exception as exc:
                last_exc = exc

                # Check if this is a quota/daily limit error
                if _is_quota_error(exc):
                    logger.error(f"Gemini API key hit daily quota limit: {exc}")
                    if current_key:
                        _mark_key_exhausted(current_key)
                    # Don't retry with this key - move to next model/key immediately
                    break

                if not _is_overload_error(exc):
                    raise  # not transient — propagate immediately

                delay = min(2 ** (attempt - 1), 16) + random.uniform(0, 1)
                logger.warning(
                    "Gemini %s overload (attempt %d/%d), retrying in %.1fs — %s",
                    model, attempt, max_retries, delay, exc,
                )
                await asyncio.sleep(delay)

        logger.warning(
            "All %d retries exhausted for model=%s, trying next fallback.",
            max_retries, model,
        )

    raise RuntimeError(
        "All Gemini models and API keys are currently unavailable. "
        "Please try again in a minute or add more API keys."
    ) from last_exc


# ---------------------------------------------------------------------------
# Public API — same prompts, now routed through _generate_with_retry
# ---------------------------------------------------------------------------

async def analyze_fridge_photo(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict[str, Any]:
    """Analyze a photo of a fridge/cupboard to identify food items and check for spoilage."""
    prompt = """You are a food inventory analyst. Analyze this photo of a fridge, cupboard, or food storage area.

For EACH food item you can identify, return a JSON object with these fields:
- name: the food item name (e.g. "whole milk", "cheddar cheese", "romaine lettuce")
- category: one of [dairy, meat, seafood, fruit, vegetable, bread, eggs, leftover, condiment, canned, dry_goods, beverage, frozen, other]
- quantity: estimated quantity (number)
- unit: unit of measure (e.g. "item", "bottle", "bag", "container", "bunch", "lb", "pack")
- is_perishable: true/false
- storage: where it appears to be stored - one of [fridge, freezer, pantry, counter]
- bbox: bounding box of this item in the image as [x1, y1, x2, y2] where all values are NORMALISED 0.0-1.0
  (x1,y1 = top-left corner, x2,y2 = bottom-right corner, relative to full image width/height).
  If you cannot locate the item precisely, omit this field or set it to null.

Also check for ANY visual signs of spoilage on visible items:
- Mold (fuzzy patches, green/white/black spots)
- Browning or discoloration that is abnormal for the item
- Wilting, sliminess, or shriveling
- Swollen packaging

Return JSON in this exact format:
{
  "items": [<list of item objects>],
  "spoilage_reports": [
    {
      "item_name": "...",
      "spoilage_detected": true/false,
      "signs": ["list of observed signs"],
      "confidence": 0.0-1.0,
      "recommendation": "what to do"
    }
  ],
  "description": "Brief overview of what you see"
}

Return ONLY valid JSON, no markdown fences."""

    text = await _generate_with_retry([
        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        types.Part.from_text(text=prompt),
    ])
    return _parse_json_response(text)


async def analyze_receipt_photo(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict[str, Any]:
    """Extract food items from a receipt photo."""
    prompt = """You are a grocery receipt parser. Analyze this receipt photo and extract ALL FOOD items including pet food.

For each food item, return:
- name: the PRODUCT NAME ONLY (e.g. "Almond Milk", "Yogurt", "Eggs"). Do NOT include size/quantity (1L, 350g, /kg) or brand abbreviations in the name. Put size/quantity in the "quantity" and "unit" fields instead.
- category: one of [dairy, meat, seafood, fruit, vegetable, bread, eggs, leftover, condiment, canned, dry_goods, beverage, frozen, other]
- quantity: quantity purchased (number, default 1)
- unit: unit of measure (e.g. "item", "lb", "oz", "gallon", "pack", "bag", "can", "box")
- is_perishable: true/false

IMPORTANT NAMING RULES:
- Product names should be clean: "Almond Milk", not "Milk Almond Uht 1L"
- Extract size into quantity+unit: "Yogurt Blueberry 150G" → name: "Yogurt Blueberry", quantity: 150, unit: "g"
- Remove brand suffixes and abbreviations from names
- Examples of clean names: "Eggs", "Onions", "Yogurt", "Bread", "Milk", "Chicken Breast", NOT "Eggs Barn 350G" or "Yog Bberry"

IMPORTANT CATEGORIZATION RULES:
- Pet food containing meat/chicken → use "meat" category 
- Pet food containing fish → use "seafood" category
- Dry pet food, pet treats → use "dry_goods" category
- Canned pet food → use "canned" category
- Fresh pet food (refrigerated) → use appropriate category (meat/seafood)
- All pet food should be marked as perishable: true (unless it's clearly shelf-stable dry food)

Examples:
- Receipt shows "Harrington Senior Chicken 400g" → name: "Chicken", quantity: 400, unit: "g", category: "meat"
- Receipt shows "Yog Blueberry 150G" → name: "Yogurt Blueberry", quantity: 150, unit: "g", category: "dairy"
- Receipt shows "Eggs Free Range 12 pack" → name: "Eggs", quantity: 12, unit: "item", category: "eggs"

Skip non-food items (bags, tax, discounts, cleaning products, etc).

Return JSON in this exact format:
{
  "items": [<list of item objects>],
  "store_name": "store name if visible",
  "date": "purchase date if visible (YYYY-MM-DD)",
  "description": "Brief summary of the receipt"
}

Return ONLY valid JSON, no markdown fences."""

    try:
        text = await _generate_with_retry([
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            types.Part.from_text(text=prompt),
        ])
        result = _parse_json_response(text)
        if "error" not in result:
            result["extraction_source"] = "gemini"
            return result
    except Exception as exc:
        logger.warning("Gemini receipt analysis failed, falling back to heuristic parser: %s", exc)

    # Gemini failed or returned unparseable JSON — use heuristic fallback parser.
    logger.info("Running receipt fallback parser based on heuristics and OCR")
    fallback_result = await receipt_fallback_service.analyze_receipt_photo(image_bytes, mime_type)
    fallback_result["extraction_source"] = "fallback_heuristic"
    fallback_result["fallback_reason"] = "gemini_failure"
    return fallback_result


async def check_spoilage(image_bytes: bytes, item_name: str, mime_type: str = "image/jpeg") -> dict[str, Any]:
    """Check a specific food item photo for visual signs of spoilage."""
    prompt = f"""You are a food safety inspector. Examine this photo of "{item_name}" for ANY signs of spoilage.

Look carefully for:
1. Mold - fuzzy patches, spots (green, white, black, blue)
2. Abnormal discoloration - browning, yellowing, dark spots that shouldn't be there
3. Texture changes - sliminess, excessive softness, shriveling, wilting
4. Packaging issues - swelling, leaking, damaged seals
5. Other signs - unusual condensation, separation, crystallization

Return JSON:
{{
  "item_name": "{item_name}",
  "spoilage_detected": true/false,
  "signs": ["list each sign observed"],
  "confidence": 0.0-1.0,
  "overall_assessment": "safe to eat" | "use immediately" | "questionable" | "do not consume",
  "recommendation": "detailed recommendation for the user"
}}

Be conservative - when in doubt, flag it. Return ONLY valid JSON, no markdown fences."""

    text = await _generate_with_retry([
        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        types.Part.from_text(text=prompt),
    ])
    return _parse_json_response(text)


async def suggest_meals(
    inventory_items: list[dict],
    meal_count: int = 3,
    dietary_prompt: str = "No dietary restrictions.",
    household_size: int = 1,
) -> list[dict]:
    safe_inventory = [i for i in inventory_items if not i.get("visual_hazard", False)]
    good_items = [i for i in safe_inventory if i.get("freshness_score", 100) >= 70]
    use_soon_items = [i for i in safe_inventory if 50 <= i.get("freshness_score", 100) < 70]
    critical_items = [i for i in safe_inventory if i.get("freshness_score", 100) < 50]

    inventory_summary = ""
    if critical_items:
        inventory_summary += "CRITICAL - Must use immediately:\n"
        for item in critical_items:
            inventory_summary += f"  - {item['name']} (freshness: {item['freshness_score']}%, {item['quantity']} {item['unit']})\n"
    if use_soon_items:
        inventory_summary += "\nUSE SOON - Should use in next few meals:\n"
        for item in use_soon_items:
            inventory_summary += f"  - {item['name']} (freshness: {item['freshness_score']}%, {item['quantity']} {item['unit']})\n"
    if good_items:
        inventory_summary += "\nGOOD - Available for any meal:\n"
        for item in good_items:
            inventory_summary += f"  - {item['name']} ({item['quantity']} {item['unit']})\n"

    portion_note = f"Portions should serve {household_size} person(s)." if household_size > 0 else ""

    prompt = f"""You are a creative home chef helping reduce food waste. Based on the inventory below, suggest {meal_count} meals.

DIETARY REQUIREMENTS (MUST follow strictly - never suggest meals that violate these):
{dietary_prompt}
{portion_note}

RULES:
1. PRIORITIZE items marked CRITICAL - these MUST be used in at least one meal
2. Items marked USE SOON should be incorporated into meals where possible
3. For CRITICAL items (freshness below 50%), also suggest alternative uses to prevent waste (e.g. overripe bananas -> banana bread, wilting herbs -> pesto, soft tomatoes -> sauce)
4. Meals should be practical and achievable for a home cook
5. Use mainly ingredients from the inventory
6. NEVER suggest meals containing ingredients that violate the dietary requirements above

INVENTORY:
{inventory_summary}

Return JSON:
{{
  "meals": [
    {{
      "name": "meal name",
      "description": "one-line description",
      "ingredients_used": ["list of inventory items used"],
      "instructions": ["step 1", "step 2", ...],
      "freshness_priority": "critical" | "use_soon" | "normal",
      "prep_time_minutes": 30
    }}
  ],
  "waste_prevention_tips": [
    {{
      "item": "item name",
      "tip": "alternative use suggestion"
    }}
  ]
}}

Return ONLY valid JSON, no markdown fences."""

    text = await _generate_with_retry([types.Part.from_text(text=prompt)])
    return _parse_json_response(text)


async def generate_shopping_list(
    inventory_items: list[dict],
    recent_meals: list[dict],
    consumption_history: list[dict],
) -> list[dict]:
    """Generate a smart shopping list based on what's been used and what's running low."""
    prompt = f"""You are a smart grocery shopping assistant. Based on the user's current inventory, recent meals, and consumption patterns, suggest items they should buy.

CURRENT INVENTORY (with freshness scores):
{json.dumps(inventory_items, indent=2, default=str)}

RECENT MEALS PLANNED/COOKED:
{json.dumps(recent_meals, indent=2, default=str)}

CONSUMPTION HISTORY (items used up recently):
{json.dumps(consumption_history, indent=2, default=str)}

Generate a shopping list with:
1. Items that have been used up in recent meals and need restocking
2. Items running very low in quantity
3. Common staples that pair well with remaining inventory
4. Items needed for balanced nutrition if the inventory is skewed

Return JSON:
{{
  "shopping_list": [
    {{
      "name": "item name",
      "category": "food category",
      "reason": "why this item is suggested",
      "urgency": "urgent" | "soon" | "normal"
    }}
  ]
}}

Return ONLY valid JSON, no markdown fences."""

    text = await _generate_with_retry([types.Part.from_text(text=prompt)])
    return _parse_json_response(text)


async def generate_weekly_meal_plan(
    inventory_items: list[dict],
    dietary_prompt: str = "No dietary restrictions.",
    household_size: int = 1,
) -> dict[str, Any]:
    """Generate a 7-day meal plan projecting freshness forward."""
    safe_inventory = [item for item in inventory_items if not item.get("visual_hazard", False)]
    items_summary = ""
    for item in safe_inventory:
        items_summary += (
            f"  - {item['name']} (category: {item['category']}, freshness: {item.get('freshness_score', 100)}%, "
            f"qty: {item['quantity']} {item['unit']}, storage: {item.get('storage', 'fridge')})\n"
        )

    prompt = f"""You are a meal planning expert minimizing food waste. Create a 7-day meal plan.

DIETARY REQUIREMENTS:
{dietary_prompt}
Portions for {household_size} person(s).

CURRENT INVENTORY:
{items_summary}

RULES:
1. Schedule meals so that items with the LOWEST freshness are used FIRST (day 1-2)
2. Project freshness forward: items lose freshness each day, so plan accordingly
3. Each day should have breakfast, lunch, and dinner
4. Minimize the need for external ingredients - use what's in the pantry
5. NEVER violate dietary requirements
6. By the end of the week, most perishable items should be used

Return JSON:
{{
  "days": [
    {{
      "day": 1,
      "date_label": "Day 1 (Today)",
      "meals": {{
        "breakfast": {{
          "name": "...",
          "ingredients_used": ["..."],
          "prep_time_minutes": 15
        }},
        "lunch": {{
          "name": "...",
          "ingredients_used": ["..."],
          "prep_time_minutes": 20
        }},
        "dinner": {{
          "name": "...",
          "ingredients_used": ["..."],
          "prep_time_minutes": 30
        }}
      }},
      "items_to_use_today": ["items that must be used today based on freshness"]
    }}
  ],
  "shopping_needed": ["any items needed that aren't in inventory"],
  "summary": "Brief overview of the plan"
}}

Return ONLY valid JSON, no markdown fences."""

    text = await _generate_with_retry([types.Part.from_text(text=prompt)])
    return _parse_json_response(text)


async def analyze_nutritional_balance(inventory_items: list[dict], recent_meals: list[dict]) -> dict[str, Any]:
    """Analyze the nutritional balance of current inventory and recent meals."""
    prompt = f"""You are a nutritionist. Analyze this person's food inventory and recent meals for nutritional balance.

CURRENT INVENTORY:
{json.dumps(inventory_items, indent=2, default=str)}

RECENT MEALS:
{json.dumps(recent_meals, indent=2, default=str)}

Evaluate across these dimensions:
1. Protein sources (meat, fish, eggs, legumes, dairy, tofu)
2. Fruits and vegetables variety
3. Whole grains and fiber
4. Healthy fats
5. Vitamins and minerals diversity
6. Overall balance

Return JSON:
{{
  "overall_score": 0-100,
  "overall_assessment": "brief assessment",
  "categories": [
    {{
      "name": "Protein",
      "score": 0-100,
      "status": "good" | "moderate" | "low",
      "detail": "explanation",
      "suggestion": "what to add"
    }}
  ],
  "missing_food_groups": ["list of food groups that are underrepresented"],
  "top_recommendations": ["actionable suggestions to improve balance"]
}}

Return ONLY valid JSON, no markdown fences."""

    text = await _generate_with_retry([types.Part.from_text(text=prompt)])
    return _parse_json_response(text)


async def parse_voice_input(text: str) -> dict[str, Any]:
    """Parse natural language voice input into structured food items."""
    today = __import__("datetime").date.today().isoformat()
    prompt = f"""You are a food item parser. The user said the following while adding items to their pantry:

"{text}"

Today's date is {today}.

Extract each food item mentioned. For each, determine:
- name: the food item
- category: one of [dairy, meat, seafood, fruit, vegetable, bread, eggs, leftover, condiment, canned, dry_goods, beverage, frozen, other]
- quantity: number (default 1)
- unit: unit of measure (item, lb, oz, gallon, pack, bunch, bag, bottle, can, box, dozen)
- is_perishable: true/false
- storage: most likely storage location [fridge, freezer, pantry, counter]
- purchase_date: an ISO date string (YYYY-MM-DD) representing WHEN the user acquired the item.

IMPORTANT CATEGORIZATION RULES:
- Pet food containing meat/chicken → use "meat" category 
- Pet food containing fish → use "seafood" category
- Dry pet food, pet treats → use "dry_goods" category
- Canned pet food → use "canned" category
- Fresh pet food (refrigerated) → use appropriate category (meat/seafood)

CRITICAL: Pay attention to BOTH purchase timing AND expiry timing mentioned in the text:
  
  For PURCHASE timing ("bought yesterday", "got last week", etc.):
  Convert those relative expressions into an actual purchase date based on today ({today}).
  
  For EXPIRY timing ("expires in 3 days", "expiring tomorrow", "goes bad in a week", "use by Friday", etc.):
  Work backwards from the expiry date to estimate when the item was likely purchased.
  Use these decay rates per day for different food categories in fridge storage:
  - meat: 8 points/day (so if expires in 3 days with ~75 freshness, bought ~3 days ago)
  - dairy: 5 points/day
  - fruit: 3.5 points/day  
  - vegetable: 3 points/day
  - seafood: 10 points/day
  - bread: 4 points/day
  - eggs: 2 points/day
  - other: 2 points/day
  
  Example: "chicken breast expiring in 3 days" = meat category, decay 8/day
  If expiring in 3 days, freshness should be ~75 (use within 3 days)
  Working back: 100 - (days_since_purchase * 8) = 75
  So: days_since_purchase = (100-75)/8 = ~3 days ago
  Purchase date = today - 3 days
  
  If no timing information is given, default to today ({today}).

Return JSON:
{{
  "items": [
    {{
      "name": "...",
      "category": "...",
      "quantity": 1,
      "unit": "item",
      "is_perishable": true,
      "storage": "fridge",
      "purchase_date": "YYYY-MM-DD"
    }}
  ],
  "unrecognized": ["anything said that doesn't seem to be a food item"]
}}

Return ONLY valid JSON, no markdown fences."""

    text = await _generate_with_retry([types.Part.from_text(text=prompt)])
    return _parse_json_response(text)

async def generate_metabolic_recipe(
    inventory_items: list[dict],
    biometrics: dict[str, Any],
    profile_data: str,
) -> dict[str, Any]:
    """
    Constraint-Driven RAG for recipes based on:
      1. Inventory freshness constraints.
      2. Biometric state of the user.
      3. User profile goals/restrictions.
    """
    # Separate inventory by freshness constraint and exclude items with visual hazards
    safe_inventory = [i for i in inventory_items if not i.get("visual_hazard", False)]
    critical_items = [i for i in safe_inventory if i.get("freshness_score", 100) < 50]
    stable_items = [i for i in safe_inventory if i.get("freshness_score", 100) >= 50]
    
    inv_summary = "CRITICAL (Must Use):\n"
    for i in critical_items:
        inv_summary += f"  - {i.get('name', 'Unknown')} (score: {i.get('freshness_score')})\n"
    inv_summary += "\nSTABLE (Can Use):\n"
    for i in stable_items:
        inv_summary += f"  - {i.get('name', 'Unknown')} (score: {i.get('freshness_score')})\n"

    prompt = f"""You are the 'Metabolic Guard', an elite constraint-driven cooking AI.
Your goal is to suggest THREE highly optimized meal recipes that perfectly balance the user's BIOLOGICAL NEEDS with their INVENTORY CONSTRAINTS.

USER PROFILE & DIET GOALS:
{profile_data}

CURRENT BIOMETRIC STATE:
{json.dumps(biometrics, indent=2)}

INVENTORY:
{inv_summary}

RULES:
1. BIOMETRIC ALIGNMENT: 
   - If Sleep/Readiness is low or Stress is high, use ingredients rich in recovery nutrients (magnesium, complex carbs, antioxidants).
   - If Steps are high, provide sufficient protein/carbs for recovery.
2. CIRCULAR OPTIMIZATION:
   - You MUST utilize at least some items from the "CRITICAL" inventory list to prevent food waste.
   - You may use "STABLE" items to round out the nutritional profile.
3. STRICT DIETARY ADHERENCE: Never violate the user's dietary restrictions or fitness goals.
4. VARIED SUGGESTIONS: Ensure the three recipes offer different flavors or types of meals (e.g. one breakfast-style, one lunch, one dinner, or different cuisines).

Return JSON in this EXACT format:
{{
  "recipes": [
    {{
      "name": "Recipe Name",
      "description": "Short description of why this recipe is perfect for their biometric state",
      "ingredients_used": ["..."],
      "instructions": ["..."],
      "prep_time_minutes": 25,
      "metabolic_alignment_score": 95,
      "justification": "Detailed explanation of how this targets their specific biometric needs."
    }}
  ]
}}

Return ONLY valid JSON, no markdown fences."""

    text = await _generate_with_retry([types.Part.from_text(text=prompt)])
    return _parse_json_response(text)


def _parse_json_response(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = lines[1:]  # remove opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.error("Failed to parse Gemini response as JSON: %s", text[:500])
        return {"error": "Failed to parse AI response", "raw": text[:500]}
