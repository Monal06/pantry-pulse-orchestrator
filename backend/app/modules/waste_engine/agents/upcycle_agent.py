"""
Upcycle Agent: Generate Creative Recipes for Critical Items

When an item has a critical freshness score (20-50) but is still salvageable,
this agent uses Gemini to generate creative recipes that:
1. Use the specific item at its current ripeness/condition
2. Require minimal additional ingredients
3. Are quick to prepare (user urgency)
4. Account for dietary restrictions (if provided)

Integration: Called after Exit Strategy orchestrator recommends UPCYCLE
"""

from typing import Optional
from app.services import gemini_service


class UpcycleAgent:
    """Generate upcycling recipes for critical freshness items"""

    @staticmethod
    async def generate_recipes(
        item_name: str,
        category: str,
        freshness_score: float,
        quantity: float,
        unit: str = "item",
        dietary_restrictions: Optional[list[str]] = None,
        available_ingredients: Optional[list[str]] = None,
    ) -> dict:
        """
        Generate creative recipes to upcycle a critical item.

        Args:
            item_name: e.g., "Overripe Banana"
            category: e.g., "fruit"
            freshness_score: 20-50 (salvageable range)
            quantity: e.g., 3
            unit: e.g., "item"
            dietary_restrictions: e.g., ["vegan", "gluten-free"]
            available_ingredients: e.g., ["flour", "eggs", "milk"]

        Returns:
            Dictionary with generated recipes and preparation tips
        """
        dietary_text = (
            f"\nUser dietary restrictions: {', '.join(dietary_restrictions)}"
            if dietary_restrictions
            else ""
        )
        available_text = (
            f"\nAvailable pantry items: {', '.join(available_ingredients)}"
            if available_ingredients
            else ""
        )

        prompt = f"""You are a creative chef specializing in food waste reduction.
A user has a critical food item that needs to be used TODAY to prevent waste.

ITEM DETAILS:
- Item: {item_name}
- Category: {category}
- Freshness Score: {freshness_score}/100 (CRITICAL - needs urgent use)
- Quantity Available: {quantity} {unit}
{dietary_text}
{available_text}

YOUR TASK:
Generate 3 creative, quick recipes that:
1. **USE THIS ITEM AT ITS CURRENT STATE** (e.g., if banana is overripe, use that fact, don't ask for fresh bananas)
2. **Require minimal prep time** (max 30 minutes, user urgency)
3. **Use common pantry staples** (don't require specialty ingredients)
4. **Are delicious AND help reduce waste** (not just "throw it in a soup")
5. **Account for dietary restrictions** (if provided)

For each recipe, return JSON with:
{{
  "name": "Recipe Name",
  "description": "Why this is perfect for overripe {item_name}",
  "ingredients": ["ingredient 1", "ingredient 2", ...],
  "instructions": ["step 1", "step 2", ...],
  "prep_time_minutes": 15,
  "urgency_level": "use-today" | "use-this-week",
  "waste_saved_kg": 0.3,
  "difficulty": "easy" | "medium",
  "tip": "Pro tip for success"
}}

Return a JSON array with 3 recipes. Be creative! (e.g., overripe fruit → smoothie, bread pudding, jam, etc.)
"""

        try:
            response = await gemini_service._generate_with_retry(
                [{"type": "text", "text": prompt}]
            )

            # Parse JSON from response
            import json
            import re

            # Extract JSON from markdown code blocks if present
            json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", response, re.DOTALL)
            json_str = json_match.group(1) if json_match else response

            recipes = json.loads(json_str)
            if not isinstance(recipes, list):
                recipes = [recipes]

            return {
                "status": "success",
                "item_name": item_name,
                "recipes": recipes,
                "message": f"Generated {len(recipes)} creative recipes to save your {item_name}!",
            }

        except Exception as e:
            return {
                "status": "error",
                "item_name": item_name,
                "error": str(e),
                "fallback_suggestions": _get_fallback_recipes(category, item_name),
            }

    @staticmethod
    async def get_storage_tips(item_name: str, category: str) -> dict:
        """Get tips on how to store item to extend shelf life slightly before cooking"""
        prompt = f"""The user has a {category} item ({item_name}) with critical freshness (< 50 score).
They're trying to save it from waste but may not cook it today.

Provide 2-3 practical tips to extend shelf life by 1-2 days (without prolonging danger).
For example: "Move to freezer if time allows" or "Store in airtight container".

Return JSON:
{{
  "storage_tips": ["tip 1", "tip 2"],
  "freezing_option": "whether item can be frozen to extend life",
  "urgency": "use-today" | "use-within-2-days"
}}
"""
        try:
            response = await gemini_service._generate_with_retry(
                [{"type": "text", "text": prompt}]
            )
            import json
            import re

            json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", response, re.DOTALL)
            json_str = json_match.group(1) if json_match else response

            return json.loads(json_str)
        except Exception as e:
            return {
                "storage_tips": ["Check instructions below recipe"],
                "error": str(e),
            }


def _get_fallback_recipes(category: str, item_name: str) -> list[dict]:
    """Fallback recipes when Gemini is unavailable"""
    fallbacks = {
        "fruit": [
            {
                "name": "Quick Smoothie",
                "description": "Blend with yogurt or milk",
                "prep_time_minutes": 5,
            },
            {
                "name": "Fruit Sauce",
                "description": "Simmer and strain for jam-like spread",
                "prep_time_minutes": 20,
            },
        ],
        "vegetable": [
            {
                "name": "Roasted Veggies",
                "description": "Toss with oil, roast at 400°F",
                "prep_time_minutes": 25,
            },
            {
                "name": "Vegetable Soup",
                "description": "Simmer with broth and seasonings",
                "prep_time_minutes": 30,
            },
        ],
        "bread": [
            {
                "name": "Bread Pudding",
                "description": "Cube, soak in milk/egg mixture, bake",
                "prep_time_minutes": 40,
            },
            {
                "name": "Croutons",
                "description": "Cube, toast with olive oil",
                "prep_time_minutes": 15,
            },
        ],
        "dairy": [
            {
                "name": "Pancakes",
                "description": "Use milk in batter",
                "prep_time_minutes": 20,
            },
        ],
        "meat": [
            {
                "name": "Stir Fry",
                "description": "Quick cook with vegetables",
                "prep_time_minutes": 20,
            },
            {
                "name": "Broth",
                "description": "Simmer to extract flavor and nutrients",
                "prep_time_minutes": 60,
            },
        ],
    }

    return fallbacks.get(category.lower(), [{"name": "Use ASAP", "description": "Cook immediately"}])
