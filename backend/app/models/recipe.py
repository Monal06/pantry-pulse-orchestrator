from __future__ import annotations

from pydantic import BaseModel


class SavedRecipe(BaseModel):
    id: str
    user_id: str
    name: str
    description: str = ""
    ingredients: list[str] = []
    instructions: list[str] = []
    prep_time_minutes: int = 30
    times_cooked: int = 0
    is_favorite: bool = False
    created_at: str = ""
