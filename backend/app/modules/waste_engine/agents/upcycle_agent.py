"""
Upcycle Agent: Creative Recipes for Critical Items

When an item has a critical freshness score (20-50) but is still salvageable,
this agent provides creative recipes from a comprehensive hardcoded database.

Instant, reliable, zero Gemini quota dependency - perfect for competition demo.

Integration: Called after Exit Strategy orchestrator recommends UPCYCLE
"""

from typing import Optional
from app.modules.waste_engine.upcycle_nonfood_uses import get_nonfood_uses


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
        Get upcycling non-food uses from comprehensive hardcoded database.

        Uses authoritative non-food uses collection (40+ uses across 20+ items).
        Instant, reliable, zero Gemini quota dependency.

        Creative ways to repurpose food items that aren't suitable for consumption:
        composting, gardening, crafts, natural dyes, pest control, etc.

        Args:
            item_name: e.g., "Overripe Banana"
            category: e.g., "fruit"
            freshness_score: 20-50 (salvageable range)
            quantity: e.g., 3
            unit: e.g., "item"
            dietary_restrictions: (optional, for future use)
            available_ingredients: (optional, for future use)

        Returns:
            Dictionary with non-food uses from hardcoded database
        """
        # Get non-food uses for this item from database
        uses = get_nonfood_uses(item_name.lower())

        # If no exact match, try category
        if not uses:
            uses = get_nonfood_uses(category.lower())

        # If still no match, use generic fallback
        if not uses:
            uses = _get_generic_fallback(category, item_name)

        print(f"[UPCYCLE-AGENT] ✓ Retrieved {len(uses)} non-food uses for {item_name}")

        return {
            "status": "success",
            "item_name": item_name,
            "uses": uses,
            "message": f"Found {len(uses)} creative ways to give new life to your {item_name}!",
        }



def _get_generic_fallback(category: str, item_name: str) -> list[dict]:
    """Generic fallback non-food uses for unknown items"""
    fallbacks = {
        "fruit": [
            {
                "title": "Compost Pile",
                "difficulty": "EASY",
                "time_mins": 10,
                "description": "Add to compost bin - fruits are excellent 'green' material",
                "steps": [
                    f"Chop {item_name} into smaller pieces",
                    "Layer in compost bin with browns (leaves, straw)",
                    "Keep moist like wrung-out sponge",
                    "Ready in 2-3 months depending on conditions"
                ]
            },
            {
                "title": "Wildlife Food",
                "difficulty": "EASY",
                "time_mins": 5,
                "description": f"Leave {item_name} scraps out for birds, insects, or wildlife",
                "steps": [
                    f"Cut {item_name} into pieces",
                    "Place in accessible outdoor area",
                    "Great for birds and hedgehogs",
                ]
            },
        ],
        "vegetable": [
            {
                "title": "Compost Pile",
                "difficulty": "EASY",
                "time_mins": 10,
                "description": "Vegetables are primary compost material ('green' materials)",
                "steps": [
                    f"Chop {item_name} into smaller pieces",
                    "Layer in compost bin with browns",
                    "Keep moist and turn occasionally",
                    "Ready in 3-6 months"
                ]
            },
            {
                "title": "Garden Fertilizer",
                "difficulty": "MEDIUM",
                "time_mins": 30,
                "description": "Bury in garden bed as slow-release fertilizer",
                "steps": [
                    "Dig 12-inch trench in garden bed",
                    f"Bury {item_name} scraps in trench",
                    "Cover with 6 inches of soil",
                    "Vegetables decompose and feed growing plants"
                ]
            },
        ],
        "bread": [
            {
                "title": "Compost It",
                "difficulty": "EASY",
                "time_mins": 5,
                "description": "Break into pieces and add to compost bin",
                "steps": [
                    "Break bread into small chunks",
                    "Add to compost bin or garden compost pile",
                    "Bread decomposes quickly and adds carbon",
                    "Helps create nutrient-rich compost in 2-3 months"
                ]
            },
            {
                "title": "Bird Feeder",
                "difficulty": "EASY",
                "time_mins": 10,
                "description": "Crumble and scatter for birds (break it up so birds don't choke)",
                "steps": [
                    "Crumble bread into small pieces",
                    "Scatter in garden or park for birds",
                    "Best in winter when food is scarce",
                ]
            },
        ],
        "dairy": [
            {
                "title": "Plant Fertilizer",
                "difficulty": "EASY",
                "time_mins": 10,
                "description": "Dilute sour dairy and use on plants for calcium",
                "steps": [
                    "Dilute with water (1:1 ratio)",
                    "Pour around plant base",
                    "Beneficial bacteria help soil health",
                    "Calcium content strengthens plants"
                ]
            },
        ],
        "meat": [
            {
                "title": "Compost (Deep Burial)",
                "difficulty": "MEDIUM",
                "time_mins": 20,
                "description": "Bury deep in compost to become excellent nitrogen source",
                "steps": [
                    "Chop meat into small pieces",
                    "Bury 12+ inches deep in compost pile",
                    "Cover well with soil/compost",
                    "Becomes excellent nitrogen source (3-4 months)"
                ]
            },
        ],
    }

    return fallbacks.get(category.lower(), [
        {
            "title": "Compost",
            "difficulty": "EASY",
            "time_mins": 5,
            "description": "Add to compost bin for nutrient-rich soil",
            "steps": ["Add to compost bin", "Layer with other materials", "Ready in 2-3 months"]
        }
    ])
