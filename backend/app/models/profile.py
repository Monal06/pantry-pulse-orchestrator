from __future__ import annotations

from pydantic import BaseModel


class DietaryProfile(BaseModel):
    vegetarian: bool = False
    vegan: bool = False
    gluten_free: bool = False
    dairy_free: bool = False
    nut_free: bool = False
    halal: bool = False
    kosher: bool = False
    low_carb: bool = False
    allergies: list[str] = []
    dislikes: list[str] = []
    cuisine_preferences: list[str] = []
    household_size: int = 1
    fitness_goals: list[str] = []  # e.g., "hypertrophy", "fat loss", "endurance", "maintenance"

    def to_prompt_string(self) -> str:
        restrictions: list[str] = []
        if self.vegetarian:
            restrictions.append("vegetarian (no meat or fish)")
        if self.vegan:
            restrictions.append("vegan (no animal products)")
        if self.gluten_free:
            restrictions.append("gluten-free")
        if self.dairy_free:
            restrictions.append("dairy-free")
        if self.nut_free:
            restrictions.append("nut-free")
        if self.halal:
            restrictions.append("halal")
        if self.kosher:
            restrictions.append("kosher")
        if self.low_carb:
            restrictions.append("low-carb")
        if self.allergies:
            restrictions.append(f"allergic to: {', '.join(self.allergies)}")
        if self.dislikes:
            restrictions.append(f"dislikes: {', '.join(self.dislikes)}")

        diet_str = "Dietary restrictions: " + "; ".join(restrictions) if restrictions else "No dietary restrictions."
        
        goals_str = "Fitness goals: " + ", ".join(self.fitness_goals) if self.fitness_goals else "No specific fitness goals."
        
        return f"{diet_str}\n{goals_str}"
