from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.services import recipe_service, gemini_service
from app.models.biometric import BiometricData
from app.models.profile import DietaryProfile
from pydantic import BaseModel
from typing import Any

class MetabolicPlanRequest(BaseModel):
    inventory_items: list[dict]
    biometrics: BiometricData
    profile: DietaryProfile


router = APIRouter(prefix="/recipes", tags=["recipes"])

DEFAULT_USER = "demo-user"


@router.get("/favorites")
async def get_favorites(user_id: str = Query(default=DEFAULT_USER)):
    """Get all favorited recipes."""
    recipes = await recipe_service.get_favorites(user_id)
    return [r.model_dump(mode="json") for r in recipes]


@router.get("")
async def get_all_recipes(user_id: str = Query(default=DEFAULT_USER)):
    """Get all saved recipes."""
    recipes = await recipe_service.get_all_recipes(user_id)
    return [r.model_dump(mode="json") for r in recipes]


@router.post("")
async def save_recipe(
    name: str = Query(...),
    description: str = Query(default=""),
    ingredients: list[str] = Query(default=[]),
    instructions: list[str] = Query(default=[]),
    prep_time_minutes: int = Query(default=30),
    user_id: str = Query(default=DEFAULT_USER),
):
    """Save a recipe from meal suggestions."""
    recipe = await recipe_service.save_recipe(
        user_id, name, description, ingredients, instructions, prep_time_minutes
    )
    return recipe.model_dump(mode="json")


@router.post("/{recipe_id}/toggle-favorite")
async def toggle_favorite(recipe_id: str, user_id: str = Query(default=DEFAULT_USER)):
    recipe = await recipe_service.toggle_favorite(user_id, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe.model_dump(mode="json")


@router.post("/{recipe_id}/cooked")
async def record_cooked(recipe_id: str, user_id: str = Query(default=DEFAULT_USER)):
    recipe = await recipe_service.record_cooked(user_id, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe.model_dump(mode="json")


@router.delete("/{recipe_id}")
async def delete_recipe(recipe_id: str, user_id: str = Query(default=DEFAULT_USER)):
    deleted = await recipe_service.delete_recipe(user_id, recipe_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return {"status": "deleted"}


@router.post("/metabolic/plan")
async def generate_metabolic_recipe_plan(request: MetabolicPlanRequest):
    """Generate a highly optimized biometric-driven recipe."""
    try:
        recipe_suggestion = await gemini_service.generate_metabolic_recipe(
            inventory_items=request.inventory_items,
            biometrics=request.biometrics.model_dump(),
            profile_data=request.profile.to_prompt_string()
        )
        return recipe_suggestion
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
