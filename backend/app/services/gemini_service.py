from __future__ import annotations

import asyncio
import json
import logging
import random
from typing import Any

from google import genai
from google.genai import types

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=get_settings().gemini_api_key)
    return _client


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
    client = _get_client()
    models = _get_models()
    max_retries = get_settings().gemini_max_retries
    last_exc: Exception | None = None

    for model in models:
        for attempt in range(1, max_retries + 1):
            try:
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
        "All Gemini models are currently unavailable after retries. "
        "Please try again in a minute."
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
    prompt = """You are a grocery receipt parser. Analyze this receipt photo and extract all FOOD items.

For each food item, return:
- name: the food item name (clean it up from receipt abbreviations)
- category: one of [dairy, meat, seafood, fruit, vegetable, bread, eggs, leftover, condiment, canned, dry_goods, beverage, frozen, other]
- quantity: quantity purchased (number, default 1)
- unit: unit of measure (e.g. "item", "lb", "oz", "gallon", "pack")
- is_perishable: true/false

Skip non-food items (bags, tax, discounts, cleaning products, etc).

Return JSON in this exact format:
{
  "items": [<list of item objects>],
  "store_name": "store name if visible",
  "date": "purchase date if visible (YYYY-MM-DD)",
  "description": "Brief summary of the receipt"
}

Return ONLY valid JSON, no markdown fences."""

    text = await _generate_with_retry([
        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        types.Part.from_text(text=prompt),
    ])
    return _parse_json_response(text)


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
    """Generate meal suggestions prioritizing items by freshness, respecting dietary restrictions."""
    good_items = [i for i in inventory_items if i.get("freshness_score", 100) >= 70]
    use_soon_items = [i for i in inventory_items if 50 <= i.get("freshness_score", 100) < 70]
    critical_items = [i for i in inventory_items if i.get("freshness_score", 100) < 50]

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
    items_summary = ""
    for item in inventory_items:
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
    prompt = f"""You are a food item parser. The user said the following while adding items to their pantry:

"{text}"

Extract each food item mentioned. For each, determine:
- name: the food item
- category: one of [dairy, meat, seafood, fruit, vegetable, bread, eggs, leftover, condiment, canned, dry_goods, beverage, frozen, other]
- quantity: number (default 1)
- unit: unit of measure (item, lb, oz, gallon, pack, bunch, bag, bottle, can, box, dozen)
- is_perishable: true/false
- storage: most likely storage location [fridge, freezer, pantry, counter]

Return JSON:
{{
  "items": [
    {{
      "name": "...",
      "category": "...",
      "quantity": 1,
      "unit": "item",
      "is_perishable": true,
      "storage": "fridge"
    }}
  ],
  "unrecognized": ["anything said that doesn't seem to be a food item"]
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
