from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.models.waste import WasteEventType
from app.services import inventory_service, gemini_service, profile_service, waste_service

router = APIRouter(prefix="/meals", tags=["meals"])

DEFAULT_USER = "demo-user"

_meal_history: dict[str, list[dict]] = {}


@router.get("/suggestions")
async def get_meal_suggestions(
    user_id: str = Query(default=DEFAULT_USER),
    count: int = Query(default=3, ge=1, le=10),
):
    """Get AI-generated meal suggestions based on current inventory and dietary preferences."""
    items = await inventory_service.get_all_items(user_id)
    if not items:
        raise HTTPException(
            status_code=404,
            detail="Your pantry is empty. Add items first to get meal suggestions.",
        )

    dietary = await profile_service.get_profile(user_id)
    inventory_dicts = [item.model_dump(mode="json") for item in items]
    result = await gemini_service.suggest_meals(
        inventory_dicts,
        meal_count=count,
        dietary_prompt=dietary.to_prompt_string(),
        household_size=dietary.household_size,
    )

    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])

    very_critical_names = {
        i.name.strip().lower()
        for i in items
        if i.visual_hazard or i.freshness_score < 40
    }

    sanitized_meals = []
    for meal in result.get("meals", []):
        ingredients = meal.get("ingredients_used", [])
        filtered_ingredients = [
            ing for ing in ingredients
            if not any(
                crit_name in ing.strip().lower() or ing.strip().lower() in crit_name
                for crit_name in very_critical_names
            )
        ]

        if ingredients and not filtered_ingredients:
            continue

        meal_copy = dict(meal)
        meal_copy["ingredients_used"] = filtered_ingredients
        sanitized_meals.append(meal_copy)

    if not sanitized_meals:
        safe_names = [i.name for i in items if not i.visual_hazard and i.freshness_score >= 40][:4]
        fallback_ingredients = safe_names if safe_names else ["rice", "eggs", "frozen vegetables"]
        sanitized_meals = [
            {
                "name": "Quick Safe Pantry Plate",
                "description": "Simple meal plan generated from safe pantry ingredients.",
                "ingredients_used": fallback_ingredients,
                "instructions": [
                    "Prep the listed safe ingredients.",
                    "Cook thoroughly and serve immediately.",
                ],
                "freshness_priority": "use_soon",
                "prep_time_minutes": 15,
            }
        ]

    return {
        "meals": sanitized_meals,
        "waste_prevention_tips": result.get("waste_prevention_tips", []),
        "inventory_summary": {
            "total_items": len(items),
            "critical_items": len([i for i in items if i.freshness_score < 50]),
            "use_soon_items": len([i for i in items if 50 <= i.freshness_score < 70]),
        },
    }


@router.post("/cooked")
async def record_cooked_meal(
    meal_name: str = Query(...),
    ingredients_used: list[str] = Query(default=[]),
    user_id: str = Query(default=DEFAULT_USER),
):
    """Record a cooked meal: auto-deducts matching items from inventory and logs waste-saved events."""
    _meal_history.setdefault(user_id, []).append({
        "meal_name": meal_name,
        "ingredients_used": ingredients_used,
    })

    deducted = []
    not_found = []

    all_items = await inventory_service.get_all_items(user_id)

    for ingredient in ingredients_used:
        ingredient_lower = ingredient.lower()
        matched = None
        for item in all_items:
            if ingredient_lower in item.name.lower() or item.name.lower() in ingredient_lower:
                matched = item
                break

        if matched:
            result = await inventory_service.use_item(user_id, matched.id, 1)
            deducted.append(matched.name)

            await waste_service.log_event(
                user_id, matched.name, matched.category, WasteEventType.SAVED, 1
            )
            await inventory_service.log_consumption(user_id, matched.name, matched.category)
        else:
            not_found.append(ingredient)
            await inventory_service.log_consumption(user_id, ingredient, "other")

    return {
        "status": "recorded",
        "meal": meal_name,
        "deducted_from_inventory": deducted,
        "not_found_in_inventory": not_found,
    }


@router.get("/history")
async def get_meal_history(user_id: str = Query(default=DEFAULT_USER)):
    return _meal_history.get(user_id, [])


@router.get("/weekly-plan")
async def get_weekly_meal_plan(user_id: str = Query(default=DEFAULT_USER)):
    """Generate a 7-day meal plan that projects freshness forward and uses items optimally."""
    items = await inventory_service.get_all_items(user_id)
    if not items:
        raise HTTPException(
            status_code=404,
            detail="Your pantry is empty. Add items first to generate a weekly plan.",
        )

    dietary = await profile_service.get_profile(user_id)
    inventory_dicts = [item.model_dump(mode="json") for item in items]
    result = await gemini_service.generate_weekly_meal_plan(
        inventory_dicts,
        dietary_prompt=dietary.to_prompt_string(),
        household_size=dietary.household_size,
    )

    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])

    return result
