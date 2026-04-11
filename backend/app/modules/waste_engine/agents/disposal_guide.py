"""
Disposal Guide Agent: Sustainable Waste Disposal Instructions

When an item is too spoiled to eat or donate,
this agent provides detailed, location-specific disposal instructions:
1. Which bin to use (brown/green/blue/black in Galway)
2. How to prepare the item safely
3. Environmental impact
4. Composting options

Integration: Called after Exit Strategy orchestrator recommends BIN
"""

import json
from typing import Optional
from google import genai
from app.services import gemini_service

types = genai.types


class DisposalGuideAgent:
    """Provide sustainable disposal instructions for spoiled items"""

    @staticmethod
    async def get_disposal_instructions(
        item_name: str,
        category: str,
        quantity: float,
        unit: str = "item",
        location: str = "Galway",
        spoilage_type: Optional[str] = None,
    ) -> dict:
        """
        Get detailed disposal instructions for a spoiled food item.

        Args:
            item_name: e.g., "Moldy Bread"
            category: e.g., "bread"
            quantity: e.g., 1
            unit: e.g., "loaf"
            location: e.g., "Galway"
            spoilage_type: e.g., "mold", "fermentation", "sliminess"

        Returns:
            Dictionary with detailed disposal steps and environmental info
        """
        spoilage_note = f" (Reason: {spoilage_type})" if spoilage_type else ""
        prompt = f"""You are an environmental waste management specialist for {location}.

A user has a spoiled food item that cannot be safely eaten or donated:
- Item: {quantity} {unit} of {item_name} ({category}){spoilage_note}

In {location}, the waste bin system is:
- BROWN BIN: Food waste (compostable/organic)
- BLUE BIN: Recyclables (paper, cardboard, plastic, glass, metal)
- BLACK BIN: General waste (non-recyclable)
- GREEN BIN: Garden waste (leaves, grass, branches)

YOUR TASK:
Provide DETAILED disposal instructions:

1. **Which bin** to use and WHY
2. **How to prepare** the item (should it be double-bagged? drained?)
3. **What NOT to do** (don't throw down sink, don't burn, etc.)
4. **Environmental impact** (how much CO2 saved by composting vs landfill?)
5. **Alternative: Home composting** (can user compost it instead?)

Return JSON:
{{
  "primary_bin": "BROWN BIN" | "BLUE BIN" | "BLACK BIN" | "GREEN BIN",
  "bin_color": "brown" | "blue" | "black" | "green",
  "reasoning": "Why this bin is appropriate",
  "preparation_steps": [
    "Step 1: ...",
    "Step 2: ..."
  ],
  "what_not_to_do": [
    "Don't throw down sink (will clog pipes)",
    "Don't leave in compost if mold present"
  ],
  "composting_option": "Whether item can go in home compost",
  "environmental_impact": "Composting saves X kg CO2 vs landfill",
  "disposal_location": "Where to find bin on collection day in {location}",
  "pickup_schedule": "Typical bin collection day/frequency"
}}

Be specific to {location} waste management practices.
"""

        try:
            response = await gemini_service._generate_with_retry(
                [types.Part.from_text(text=prompt)]
            )

            import re

            json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", response, re.DOTALL)
            json_str = json_match.group(1) if json_match else response

            instructions = json.loads(json_str)
            if isinstance(instructions, list):
                instructions = instructions[0] if instructions else {}

            return {
                "status": "success",
                "item_name": item_name,
                "instructions": instructions,
                "message": f"Disposal guide for {item_name} — sustainable & safe",
            }

        except Exception as e:
            # Return fallback disposal on any error
            fallback = _get_fallback_disposal(category, location)
            return {
                "status": "success",  # Still return 200 with fallback data
                "item_name": item_name,
                "instructions": fallback,  # Key name that UI expects
                "message": f"Using fallback disposal guide (AI service temporarily unavailable)",
            }

    @staticmethod
    async def get_prevention_tips(
        item_name: str, category: str, reason_spoiled: Optional[str] = None
    ) -> dict:
        """
        Get tips to prevent this item from spoiling in the future.
        Called after disposal so user learns for next time.
        """
        reason_text = f" (it spoiled because: {reason_spoiled})" if reason_spoiled else ""

        prompt = f"""The user just had to dispose of {item_name} ({category}){reason_text}.

Provide 4-5 practical prevention tips they can use NEXT TIME to avoid waste:
1. Storage improvements (where/how to store it)
2. Inventory management (track what you buy)
3. Meal planning (plan recipes around expiration)
4. Freezing tips (when to freeze to extend life)
5. Freshness checks (how to check before cooking)

Return JSON:
{{
  "prevention_tips": ["tip 1", "tip 2", ...],
  "storage_location_best": "Where to store for longest life",
  "shelf_life_expected": "How many days it should last",
  "warning_signs": ["sign 1", "sign 2"] for detecting spoilage early
}}
"""

        try:
            response = await gemini_service._generate_with_retry(
                [types.Part.from_text(text=prompt)]
            )
            import re

            json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", response, re.DOTALL)
            json_str = json_match.group(1) if json_match else response

            return json.loads(json_str)
        except Exception as e:
            return {
                "prevention_tips": [
                    "Store in coolest part of fridge",
                    "Track purchase date",
                    "Use FIFO (first in, first out)",
                ],
                "error": str(e),
            }

    @staticmethod
    async def estimate_environmental_impact(
        item_name: str,
        category: str,
        quantity: float,
        bin_type: str = "BROWN",
    ) -> dict:
        """
        Estimate environmental impact of disposal method.
        """
        prompt = f"""Estimate the environmental impact of disposing {quantity} units of {item_name} ({category}).

Compare these disposal methods:
1. BROWN BIN (composted/food waste)
2. BLACK BIN (landfill)
3. HOME COMPOSTING (if applicable)
4. INCINERATION (if used in region)

For each method, estimate:
- CO2 emissions (kg)
- Methane produced (if applicable)
- Environmental benefit of each method

Return JSON:
{{
  "item": "{item_name}",
  "quantity_kg_estimated": 0.5,
  "disposal_methods": [
    {{
      "method": "BROWN BIN (composted)",
      "co2_kg": 0.1,
      "methane_kg": 0.0,
      "best_for": "Most food waste"
    }},
    {{
      "method": "BLACK BIN (landfill)",
      "co2_kg": 0.8,
      "methane_kg": 0.3,
      "best_for": "Non-compostable"
    }}
  ],
  "recommended_method": "BROWN BIN",
  "carbon_saved_vs_landfill": "0.7 kg CO2"
}}
"""

        try:
            response = await gemini_service._generate_with_retry(
                [types.Part.from_text(text=prompt)]
            )
            import re

            json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", response, re.DOTALL)
            json_str = json_match.group(1) if json_match else response

            return json.loads(json_str)
        except Exception as e:
            return {
                "status": "error",
                "message": "Could not calculate impact",
                "error": str(e),
            }


def _get_fallback_disposal(category: str, location: str = "Galway") -> dict:
    """Fallback disposal instructions when Gemini unavailable"""
    fallbacks = {
        "seafood": {
            "primary_bin": "BROWN BIN",
            "bin_color": "brown",
            "reasoning": "Food waste - compostable",
            "preparation_steps": [
                "Drain excess liquid (can pour down drain with water)",
                "Place in brown bin",
            ],
            "what_not_to_do": [
                "Don't throw shells in regular waste",
                "Don't leave uncovered (smell/pests)",
            ],
        },
        "meat": {
            "primary_bin": "BROWN BIN",
            "bin_color": "brown",
            "reasoning": "Food waste - compostable",
            "preparation_steps": [
                "Wrap in newspaper if liquid",
                "Place in brown bin",
            ],
            "what_not_to_do": ["Don't flush down toilet"],
        },
        "dairy": {
            "primary_bin": "BROWN BIN",
            "bin_color": "brown",
            "reasoning": "Food waste - compostable",
            "preparation_steps": [
                "Pour milk down drain (with water to dilute)",
                "Solid dairy → brown bin",
            ],
            "what_not_to_do": ["Don't pour large amounts of milk without water"],
        },
        "fruit": {
            "primary_bin": "BROWN BIN",
            "bin_color": "brown",
            "reasoning": "Organic compostable waste",
            "preparation_steps": ["Place directly in brown bin"],
            "composting_option": "Yes - excellent for home compost",
        },
        "vegetable": {
            "primary_bin": "BROWN BIN",
            "bin_color": "brown",
            "reasoning": "Organic compostable waste",
            "preparation_steps": ["Place directly in brown bin"],
            "composting_option": "Yes - excellent for home compost",
        },
        "bread": {
            "primary_bin": "BROWN BIN",
            "bin_color": "brown",
            "reasoning": "Food waste - compostable",
            "preparation_steps": ["Place in brown bin (mold is fine for composting)"],
            "composting_option": "Yes",
        },
    }

    return fallbacks.get(category.lower(), {
        "primary_bin": "BROWN BIN",
        "bin_color": "brown",
        "reasoning": "Most food waste goes in BROWN BIN for composting",
    })
