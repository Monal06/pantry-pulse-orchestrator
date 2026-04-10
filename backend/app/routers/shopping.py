from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.services import inventory_service, gemini_service
from app.routers.meals import _meal_history

router = APIRouter(prefix="/shopping", tags=["shopping"])

DEFAULT_USER = "demo-user"


@router.get("/list")
async def get_shopping_list(user_id: str = Query(default=DEFAULT_USER)):
    """Generate a smart shopping list based on inventory, meals, and consumption history."""
    items = await inventory_service.get_all_items(user_id)
    consumption = await inventory_service.get_consumption_history(user_id)
    meals = _meal_history.get(user_id, [])

    inventory_dicts = [item.model_dump(mode="json") for item in items]

    if not consumption and not meals:
        return {
            "shopping_list": [],
            "message": "Start using items and cooking meals to get smart shopping suggestions.",
        }

    result = await gemini_service.generate_shopping_list(
        inventory_items=inventory_dicts,
        recent_meals=meals,
        consumption_history=consumption,
    )

    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])

    return {
        "shopping_list": result.get("shopping_list", []),
        "based_on": {
            "current_items": len(items),
            "meals_cooked": len(meals),
            "items_consumed": len(consumption),
        },
    }
