from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from app.models.recipe import SavedRecipe

_recipes: dict[str, list[SavedRecipe]] = {}


async def save_recipe(
    user_id: str,
    name: str,
    description: str = "",
    ingredients: list[str] | None = None,
    instructions: list[str] | None = None,
    prep_time_minutes: int = 30,
) -> SavedRecipe:
    recipe = SavedRecipe(
        id=str(uuid4()),
        user_id=user_id,
        name=name,
        description=description,
        ingredients=ingredients or [],
        instructions=instructions or [],
        prep_time_minutes=prep_time_minutes,
        is_favorite=True,
        created_at=datetime.utcnow().isoformat(),
    )
    _recipes.setdefault(user_id, []).append(recipe)
    return recipe


async def get_favorites(user_id: str) -> list[SavedRecipe]:
    return [r for r in _recipes.get(user_id, []) if r.is_favorite]


async def get_all_recipes(user_id: str) -> list[SavedRecipe]:
    return _recipes.get(user_id, [])


async def toggle_favorite(user_id: str, recipe_id: str) -> SavedRecipe | None:
    for recipe in _recipes.get(user_id, []):
        if recipe.id == recipe_id:
            recipe.is_favorite = not recipe.is_favorite
            return recipe
    return None


async def record_cooked(user_id: str, recipe_id: str) -> SavedRecipe | None:
    for recipe in _recipes.get(user_id, []):
        if recipe.id == recipe_id:
            recipe.times_cooked += 1
            return recipe
    return None


async def delete_recipe(user_id: str, recipe_id: str) -> bool:
    recipes = _recipes.get(user_id, [])
    for i, recipe in enumerate(recipes):
        if recipe.id == recipe_id:
            recipes.pop(i)
            return True
    return False
